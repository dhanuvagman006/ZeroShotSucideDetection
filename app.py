import os
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from flask_socketio import SocketIO, emit
import base64
import threading
from werkzeug.utils import secure_filename

# Lazy import detection module when needed to avoid requiring API key on startup

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret'  # replace for production
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')
    app.config['UPLOAD_FOLDER'] = str(Path('uploads'))
    app.config['ANNOTATED_FOLDER'] = str(Path('annotated'))
    app.config['ALLOWED_EXTENSIONS'] = {'.jpg', '.jpeg', '.png'}

    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['ANNOTATED_FOLDER']).mkdir(exist_ok=True)

    def allowed_file(filename: str) -> bool:
        return Path(filename).suffix.lower() in app.config['ALLOWED_EXTENSIONS']

    # --- Auth helpers ---
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
        images = []
        for img_path in sorted(Path(app.config['UPLOAD_FOLDER']).glob('*')):
            if img_path.suffix.lower() not in app.config['ALLOWED_EXTENSIONS']:
                continue
            annotated_name = img_path.stem + '_annotated' + img_path.suffix
            annotated_path = Path(app.config['ANNOTATED_FOLDER']) / annotated_name
            images.append({
                'original': img_path.name,
                'annotated': annotated_name if annotated_path.exists() else None
            })
        return render_template('index.html', images=images, auth_enabled=auth_enabled(), logged_in=logged_in())

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

    @app.route('/camera')
    @require_auth
    def camera():
        return render_template('camera.html', auth_enabled=auth_enabled(), logged_in=logged_in())

    @app.route('/realtime')
    @require_auth
    def realtime():
        """Page that subscribes to external websocket video stream (sender.py)."""
        return render_template('realtime.html', auth_enabled=auth_enabled(), logged_in=logged_in())

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
            header, _, encoded = b64.partition(',')  # data URL or raw
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

    # --- WebSocket state ---
    client_busy = set()  # track sid of clients with active detection
    lock = threading.Lock()

    @socketio.on('frame')
    def on_frame(data):
        if auth_enabled() and not logged_in():
            emit('error', {'error': 'unauthorized'})
            return
        sid = request.sid
        with lock:
            if sid in client_busy:
                return  # drop frame (throttle)
            client_busy.add(sid)
        img_b64 = data.get('image')
        prompt = data.get('prompt')
        header, _, encoded = img_b64.partition(',')
        try:
            raw = base64.b64decode(encoded or img_b64)
        except Exception as e:
            with lock: client_busy.discard(sid)
            emit('error', {'error': 'decode failed'})
            return
        def worker():
            from detector import detect_boxes
            try:
                boxes, size = detect_boxes(raw, prompt=prompt)
                socketio.emit('boxes', {'boxes': boxes, 'size': size}, to=sid)
            except Exception as e:  # noqa
                socketio.emit('error', {'error': str(e)}, to=sid)
            finally:
                with lock:
                    client_busy.discard(sid)
        threading.Thread(target=worker, daemon=True).start()
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
