# Zero Shot Detection Web

A lightweight Flask web app to upload images, run Gemini (Google Generative AI) visual detection, and view original + annotated images in a gallery.

## Features
- Upload one or more images (JPG/PNG)
- Optional run of detection on upload (produces annotated copy)
- Gallery view with side-by-side original & annotated (if available)
- Simple, dependency-light UI
- Realtime in-browser camera capture with periodic frame detection and overlay boxes
 - WebSocket streaming for lower latency camera detection (auto fallback to HTTP)
 - Basic optional authentication (env credentials)
 - Image deletion (original + annotated) when authenticated
 - Per-client throttling to avoid overlapping model calls
 - FPS (average) overlay on camera page

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

### Realtime Camera Mode
1. Navigate to the Camera tab (nav link at top).
2. Allow browser camera permission.
3. Optionally edit the prompt.
4. Click Start to begin periodic detection (default interval 1800 ms). Click Stop to pause.
5. Bounding boxes and labels render on the canvas overlay; no frames are stored server-side.

Adjust interval lower for faster refresh (higher API usage / cost). With WebSockets the server still throttles to one in-flight detection per client.

### WebSocket vs HTTP Fallback
The client attempts to establish a Socket.IO connection. If successful, each returned detection immediately triggers the next frame send, maximizing throughput without overlapping inference. If WebSocket fails, the page falls back to timed HTTP POST requests.

### Authentication (Optional)
Set environment variables to enable login:
```
APP_USERNAME=admin
APP_PASSWORD=secret
```
If unset, the site is open (no auth). When enabled, all main routes require login. Logout link appears in nav.

### Deleting Images
Authenticated users get a Delete button per image card that removes original and matching annotated file (if present).

### Environment Variables Summary
| Name | Purpose |
|------|---------|
| GOOGLE_API_KEY | Gemini API key (required for detection) |
| MODEL_NAME | Override model id (optional) |
| APP_USERNAME | Enable auth username (optional) |
| APP_PASSWORD | Enable auth password (optional) |

### Overload / Retry Handling
The detection layer implements exponential backoff (up to 4 retries) for transient 503 / UNAVAILABLE / overloaded errors from the model API. Upload page flash messages distinguish overload from other failures. Adjust retry parameters in `detector.py` (`_generate_with_retry`).

### Running with SocketIO
When using `socketio.run(app)` development server is fine for local tests. For production consider `gunicorn -k eventlet -w 1 app:app` (adjust for create_app signature) or a production ASGI stack.

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

### Realtime Stream (External WebSocket)

An additional "Realtime" navigation link has been added which allows the browser to subscribe to a raw camera stream served by `sender.py` (stand‑alone websockets server, port 8765).

To try it:

1. In a separate terminal start the frame publisher:
   ```bash
   python sender.py
   ```
2. (Optional) Start one or more receivers with `python reciver.py` to view via OpenCV.
3. With the Flask app running, click the "Realtime" link in the top navigation.
4. Click Connect – you should see live frames (base64 JPEG) updating. Open multiple tabs to test multi‑subscriber broadcasting.

If the page does not connect, ensure nothing else is using port 8765 and that `sender.py` printed "Server started at ws://localhost:8765".
