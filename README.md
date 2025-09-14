# Zero Shot Suicidal Detection Web# Zero Shot Detection Web



A lightweight Flask web app for real-time suicidal behavior detection using Google Gemini AI and WebSocket camera streaming.A lightweight Flask web app to upload images, run Gemini (Google Generative AI) visual detection, and view original + annotated images in a gallery.



## 🎯 Features## Features

- **Live Suicidal Detection**: Auto-starts on homepage, monitors WebSocket camera feed every 5 seconds- Upload one or more images (JPG/PNG)

- **Upload Gallery**: Upload images for batch analysis with annotated results- Optional run of detection on upload (produces annotated copy)

- **Real-time Alerts**: Audio beep and visual alerts when concerning behavior is detected- Gallery view with side-by-side original & annotated (if available)

- **Dark Mode UI**: Professional monitoring interface optimized for continuous use- Simple, dependency-light UI

- **WebSocket Integration**: Uses external camera stream (no browser camera permissions needed)- Realtime in-browser camera capture with periodic frame detection and overlay boxes

- **Optional Authentication**: Environment-based login system - WebSocket streaming for lower latency camera detection (auto fallback to HTTP)

 - Basic optional authentication (env credentials)

## 🚀 Quick Start - Image deletion (original + annotated) when authenticated

 - Per-client throttling to avoid overlapping model calls

### Prerequisites - FPS (average) overlay on camera page

- Python 3.9+ # Zero Shot Suicidal Detection Web

- Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

A lightweight Flask web app for real-time suicidal behavior detection using Google Gemini AI and WebSocket camera streaming.

### Installation

```bash## Features

# Clone repository- **Live Suicidal Detection**: Auto-starts on homepage, monitors WebSocket camera feed every 5 seconds

git clone <your-repo-url>- **Upload Gallery**: Upload images for batch analysis with annotated results

cd ZeroShotSucideDetection- **Real-time Alerts**: Audio beep and visual alerts when concerning behavior is detected

- **Dark Mode UI**: Professional monitoring interface optimized for continuous use

# Install dependencies- **WebSocket Integration**: Uses external camera stream (no browser camera permissions needed)

uv sync- **Optional Authentication**: Environment-based login system

# OR: pip install -r requirements.txt

## Quick Start

# Set Google API key

$env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"### Prerequisites

```- Python 3.9+

- Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Running

```bash### Installation

# Terminal 1: Start camera WebSocket server```bash

python sender.py# Clone repository

git clone <your-repo-url>

# Terminal 2: Start web application  cd ZeroShotSucideDetection

python app.py

```# Install dependencies

uv sync

### Access# OR: pip install -r requirements.txt

- **Live Detection**: http://127.0.0.1:5000 (auto-starts monitoring)

- **Gallery**: http://127.0.0.1:5000/gallery (upload & batch analysis)# Set Google API key

$env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"

## 🔧 Technical Details```



### Core Components### Running

- **`app.py`** - Flask web application with routes and API endpoints```bash

- **`detector.py`** - Google Gemini AI integration for risk assessment# Terminal 1: Start camera WebSocket server

- **`sender.py`** - WebSocket camera server (broadcasts frames to clients)python sender.py

- **`scan.js`** - Frontend JavaScript for WebSocket connection and analysis

- **`style.css`** - Dark mode UI styling# Terminal 2: Start web application  

python app.py

### Environment Variables```

| Variable | Required | Description |

|----------|----------|-------------|### Access

| `GOOGLE_API_KEY` | Yes | Gemini API key for detection |- **Live Detection**: http://127.0.0.1:5000 (auto-starts monitoring)

| `MODEL_NAME` | No | Override model (default: gemini-2.5-flash-preview-05-20) |- **Gallery**: http://127.0.0.1:5000/gallery (upload & batch analysis)

| `APP_USERNAME` | No | Enable authentication username |

| `APP_PASSWORD` | No | Enable authentication password |## Setup

1. Create & activate a Python 3.9+ environment.

### API Endpoints2. Install dependencies (with uv):

- **`POST /api/risk_frame`** - Analyze single frame for suicidal risk```

- **`POST /api/capture_and_save`** - Save frame and run detection  uv sync

- **`POST /upload`** - Batch upload images for analysis```

   Or with pip:

### File Structure```

```pip install -e .

├── app.py              # Main Flask application```

├── detector.py         # AI detection module3. Set your Google API key (NEVER hardcode):

├── sender.py          # WebSocket camera server```

├── static/# PowerShell

│   ├── scan.js        # Live detection frontendenv:GOOGLE_API_KEY="YOUR_KEY_HERE"

│   └── style.css      # Dark mode styling```

├── templates/

│   ├── scan.html      # Live detection page## Run

│   ├── index.html     # Gallery page```

│   ├── layout.html    # Base templatepython app.py

│   └── login.html     # Authentication```

├── uploads/           # Uploaded imagesVisit http://127.0.0.1:5000

└── annotated/         # AI-processed images

```### Realtime Camera Mode

1. Navigate to the Camera tab (nav link at top).

## 🛡️ How It Works2. Allow browser camera permission.

3. Optionally edit the prompt.

1. **WebSocket Stream**: `sender.py` captures camera frames and broadcasts via WebSocket4. Click Start to begin periodic detection (default interval 1800 ms). Click Stop to pause.

2. **Auto-Detection**: Homepage connects to WebSocket and analyzes frames every 5 seconds5. Bounding boxes and labels render on the canvas overlay; no frames are stored server-side.

3. **AI Analysis**: Each frame sent to Google Gemini with specialized suicidal detection prompt

4. **Real-time Alerts**: Audio beep + visual indicators when risk threshold exceededAdjust interval lower for faster refresh (higher API usage / cost). With WebSockets the server still throttles to one in-flight detection per client.

5. **Continuous Monitoring**: Runs indefinitely until manually stopped

### WebSocket vs HTTP Fallback

## 🔒 Security NotesThe client attempts to establish a Socket.IO connection. If successful, each returned detection immediately triggers the next frame send, maximizing throughput without overlapping inference. If WebSocket fails, the page falls back to timed HTTP POST requests.



- Set authentication credentials for production use### Authentication (Optional)

- Validates file extensions only (consider MIME type checking for production)Set environment variables to enable login:

- Internal prompts designed specifically for suicidal behavior detection```

- No frames stored on server during live monitoringAPP_USERNAME=admin

APP_PASSWORD=secret

## 📝 License```

MITIf unset, the site is open (no auth). When enabled, all main routes require login. Logout link appears in nav.

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

### 5-Second Risk Scan Page

Use the new "5s Scan" nav link for a rapid assessment:

1. **Auto-start**: The page automatically starts the camera and begins detection 2 seconds after loading.
2. **Continuous monitoring**: Captures frames every 5 seconds and sends each to `/api/risk_frame` with an internal suicidal detection prompt.
3. **Real-time logging**: Each frame's risk score and indicators are logged with timestamps in the panel.
4. **Immediate alerts**: If any frame crosses the threshold (default 0.5) OR any indicators appear, a short beep sounds immediately and the video border flashes red.
5. **Visual feedback**: Status updates show camera access, detection progress, and any risk alerts.

You can adjust the threshold as needed. The page uses an internal prompt specifically designed to detect suicidal signs - no user input required. This page does not save frames.
