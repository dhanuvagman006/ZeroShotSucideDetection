import os
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from werkzeug.utils import secure_filename

# Lazy import detection module when needed to avoid requiring API key on startup

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret'  # replace for production
    app.config['UPLOAD_FOLDER'] = str(Path('uploads'))
    app.config['ANNOTATED_FOLDER'] = str(Path('annotated'))
    app.config['ALLOWED_EXTENSIONS'] = {'.jpg', '.jpeg', '.png'}

    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['ANNOTATED_FOLDER']).mkdir(exist_ok=True)

    def allowed_file(filename: str) -> bool:
        return Path(filename).suffix.lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/')
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
        return render_template('index.html', images=images)

    @app.route('/upload', methods=['POST'])
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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
