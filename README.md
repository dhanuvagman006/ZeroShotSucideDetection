# Zero Shot Detection Web

A lightweight Flask web app to upload images, run Gemini (Google Generative AI) visual detection, and view original + annotated images in a gallery.

## Features
- Upload one or more images (JPG/PNG)
- Optional run of detection on upload (produces annotated copy)
- Gallery view with side-by-side original & annotated (if available)
- Simple, dependency-light UI

## Setup
1. Create & activate a Python 3.9+ environment.
2. Install dependencies (with uv):
```
uv sync
```
   Or with pip:
```
pip install -e .
```
3. Set your Google API key (NEVER hardcode):
```
# PowerShell
env:GOOGLE_API_KEY="YOUR_KEY_HERE"
```

## Run
```
python app.py
```
Visit http://127.0.0.1:5000

## Environment Variables
- `GOOGLE_API_KEY` (required for detection)
- `MODEL_NAME` (optional override, default gemini-2.5-flash-preview-05-20)

## File Storage
Uploaded images stored under `uploads/`.
Annotated images stored under `annotated/` with same stem + `_annotated` suffix.

## Security Notes
- This demo does not implement authentication. Do not expose publicly without adding auth and validation.
- Validates file extensions only (basic). Consider MIME type checking for production.

## Roadmap / Ideas
- Multi-prompt selection
- Async background processing
- Drag & drop upload
- Delete images button

## License
MIT
