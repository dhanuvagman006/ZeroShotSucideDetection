import os
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from flask_socketio import SocketIO
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from alerting import notify_risk_detection

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret'
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')
    app.config['UPLOAD_FOLDER'] = str(Path('uploads'))
    app.config['ANNOTATED_FOLDER'] = str(Path('annotated'))
    app.config['GALLERY_FOLDER'] = str(Path('gallery'))
    app.config['ALLOWED_EXTENSIONS'] = {'.jpg', '.jpeg', '.png'}

    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['ANNOTATED_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['GALLERY_FOLDER']).mkdir(exist_ok=True)

    def allowed_file(filename: str) -> bool:
        return Path(filename).suffix.lower() in app.config['ALLOWED_EXTENSIONS']

    def auth_enabled():
        return bool(os.getenv('APP_USERNAME') and os.getenv('APP_PASSWORD'))

    def logged_in():
        return session.get('auth') is True

    from functools import wraps
    def require_auth(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if auth_enabled() and not logged_in():
                return redirect(url_for('login', next=request.path))
            return f(*args, **kwargs)
        return wrapper

    @app.route('/')
    @require_auth
    def index():
        return render_template('scan.html', auth_enabled=auth_enabled(), logged_in=logged_in())
    
    @app.route('/gallery')
    @require_auth
    def gallery():
        risk_images = []
        gallery_path = Path(app.config['GALLERY_FOLDER'])
        for img_path in sorted(gallery_path.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True):
            if img_path.suffix.lower() not in app.config['ALLOWED_EXTENSIONS']:
                continue
            metadata_path = img_path.with_suffix('.json')
            metadata = {}
            if metadata_path.exists():
                import json
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                except:
                    metadata = {}
            
            risk_images.append({
                'filename': img_path.name,
                'timestamp': metadata.get('timestamp', 'Unknown'),
                'score': metadata.get('score', 0),
                'indicators': metadata.get('indicators', [])
            })
        
        return render_template('gallery.html', 
                             risk_images=risk_images, 
                             auth_enabled=auth_enabled(), 
                             logged_in=logged_in())

    @app.route('/upload', methods=['POST'])
    @require_auth
    def upload():
        if 'images' not in request.files:
            flash('No files part')
            return redirect(url_for('index'))
        files = request.files.getlist('images')
        run_detection = request.form.get('run_detection') == 'on'
        prompt = request.form.get('prompt') or 'Detect objects.'
        count = 0
        for file in files:
            if file.filename == '':
                continue
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = Path(app.config['UPLOAD_FOLDER']) / filename
                file.save(save_path)
                count += 1
                if run_detection:
                    try:
                        from detector import run_detection as detect  # local import
                        detect(
                            image_path=str(save_path),
                            output_dir=app.config['ANNOTATED_FOLDER'],
                            prompt=prompt
                        )
                    except Exception as e:
                        msg = str(e)
                        if '503' in msg or 'UNAVAILABLE' in msg.upper() or 'overloaded' in msg.lower():
                            flash(f'Model overloaded while processing {filename}; will retry later or try again manually.')
                        else:
                            flash(f'Detection failed for {filename}: {e}')
            else:
                flash(f'Skipped unsupported file: {file.filename}')
        flash(f'Uploaded {count} file(s).')
        return redirect(url_for('index'))

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/annotated/<path:filename>')
    def annotated_file(filename):
        return send_from_directory(app.config['ANNOTATED_FOLDER'], filename)

    @app.route('/gallery/<path:filename>')
    def gallery_file(filename):
        return send_from_directory(app.config['GALLERY_FOLDER'], filename)

    @app.route('/delete', methods=['POST'])
    @require_auth
    def delete_image():
        name = request.form.get('name')
        if not name:
            flash('No file specified')
            return redirect(url_for('index'))
        orig = Path(app.config['UPLOAD_FOLDER']) / name
        ann = Path(app.config['ANNOTATED_FOLDER']) / (Path(name).stem + '_annotated' + Path(name).suffix)
        removed = []
        for p in (orig, ann):
            try:
                if p.exists():
                    p.unlink()
                    removed.append(p.name)
            except Exception as e:
                flash(f'Error deleting {p.name}: {e}')
        if removed:
            flash('Deleted: ' + ', '.join(removed))
        else:
            flash('Nothing deleted')
        return redirect(url_for('index'))

    @app.route('/api/detect_frame', methods=['POST'])
    @require_auth
    def api_detect_frame():
        try:
            data = request.get_json(force=True)
            b64 = data.get('image')
            prompt = data.get('prompt')
            if not b64:
                return {'error': 'image missing'}, 400
            import base64, traceback
            header, _, encoded = b64.partition(',')
            try:
                raw = base64.b64decode(encoded or b64)
            except Exception as e:
                print('Base64 decode error:', e)
                return {'error': 'invalid base64'}, 400
            try:
                from detector import detect_boxes
                boxes, size = detect_boxes(raw, prompt=prompt)
                return {'boxes': boxes, 'size': size}
            except Exception as e:
                print('Detection error:', e)
                traceback.print_exc()
                return {'error': f'detection failed: {e}'}, 500
        except Exception as e:
            print('API detect_frame error (outer):', e)
            return {'error': f'api error: {e}'}, 500

    @app.route('/api/risk_frame', methods=['POST'])
    @require_auth
    def api_risk_frame():
        try:
            data = request.get_json(force=True)
            if not data:
                return {'error': 'no json'}, 400
            b64 = data.get('image')
            if not b64:
                return {'error': 'image missing'}, 400
            header, _, encoded = b64.partition(',')
            try:
                raw = base64.b64decode(encoded or b64)
            except Exception:
                return {'error': 'invalid base64'}, 400
            from detector import assess_risk
            result = assess_risk(raw)
            notify_risk_detection(
                score=result.get('score', 0.0),
                indicators=result.get('indicators'),
                source='api_risk_frame',
                image_bytes=raw,
                filename='live-frame.jpg',
                extra={
                    'endpoint': '/api/risk_frame',
                    'client_ip': request.remote_addr or 'unknown',
                },
            )
            from datetime import datetime, timezone
            result['timestamp'] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:  # noqa
            return {'error': str(e)}, 500

    @app.route('/api/capture_and_save', methods=['POST'])
    @require_auth
    def api_capture_and_save():
        try:
            data = request.get_json(force=True)
            if not data:
                return {'error': 'no json'}, 400
            b64 = data.get('image')
            prompt = data.get('prompt') or 'Detect objects.'
            run_det = bool(data.get('run_detection', True))
            save_to_gallery = bool(data.get('save_to_gallery', False))
            metadata = data.get('metadata', {})
            
            if not b64:
                return {'error': 'image missing'}, 400
            header, _, encoded = b64.partition(',')
            try:
                raw = base64.b64decode(encoded or b64)
            except Exception:
                return {'error': 'invalid base64'}, 400

            import time
            fname = f"frame_{int(time.time()*1000)}.jpg"

            if save_to_gallery:
                save_path = Path(app.config['GALLERY_FOLDER']) / fname
                metadata_path = save_path.with_suffix('.json')
                import json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            else:
                save_path = Path(app.config['UPLOAD_FOLDER']) / fname
            
            with open(save_path, 'wb') as f:
                f.write(raw)
            
            annotated_name = None
            if run_det:
                try:
                    from detector import run_detection as do_detect
                    out_path = do_detect(str(save_path), app.config['ANNOTATED_FOLDER'], prompt=prompt)
                    annotated_name = Path(out_path).name
                except Exception as e:  
                    print('capture_and_save detection error:', e)
            return {'original': fname, 'annotated': annotated_name}
        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/api/upload_and_analyze', methods=['POST'])
    @require_auth
    def api_upload_and_analyze():
        """Upload a custom photo and analyze it for risk assessment."""
        try:
            if 'image' not in request.files:
                return {'error': 'No image file provided'}, 400
                
            file = request.files['image']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
                
            if not allowed_file(file.filename):
                return {'error': 'Invalid file type'}, 400

            import time
            filename = secure_filename(file.filename)
            base_name = Path(filename).stem
            ext = Path(filename).suffix
            timestamped_name = f"{base_name}_{int(time.time()*1000)}{ext}"
            
            upload_path = Path(app.config['UPLOAD_FOLDER']) / timestamped_name
            file.save(upload_path)
            
            with open(upload_path, 'rb') as f:
                image_data = f.read()
            
            from detector import assess_risk
            result = assess_risk(image_data)

            should_save = result.get('score', 0) >= 0.5 or bool(result.get('indicators', []))
            if should_save:
                gallery_path = Path(app.config['GALLERY_FOLDER']) / timestamped_name
                import shutil
                shutil.copy2(upload_path, gallery_path)
                
                import json
                from datetime import datetime, timezone
                metadata = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'score': result.get('score', 0),
                    'indicators': result.get('indicators', []),
                    'source': 'upload'
                }
                metadata_path = gallery_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            notify_risk_detection(
                score=result.get('score', 0.0),
                indicators=result.get('indicators'),
                source='api_upload_and_analyze',
                image_path=str(upload_path),
                filename=timestamped_name,
                extra={
                    'endpoint': '/api/upload_and_analyze',
                    'client_ip': request.remote_addr or 'unknown',
                    'saved_to_gallery': str(bool(should_save)),
                },
            )

            result['filename'] = timestamped_name
            return result
            
        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/login', methods=['GET','POST'])
    def login():
        if not auth_enabled():
            return redirect(url_for('index'))
        error = None
        if request.method == 'POST':
            username = request.form.get('username','')
            password = request.form.get('password','')
            if username == os.getenv('APP_USERNAME') and password == os.getenv('APP_PASSWORD'):
                session['auth'] = True
                return redirect(request.args.get('next') or url_for('index'))
            else:
                error = 'Invalid credentials'
        return render_template('login.html', error=error)

    @app.route('/logout')
    def logout():
        session.pop('auth', None)
        return redirect(url_for('login') if auth_enabled() else url_for('index'))

    return app, socketio


if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True)
