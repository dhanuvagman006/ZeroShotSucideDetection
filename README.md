# Zero-Shot Suicidal Risk Detection (Web App)

> Lightweight Flask application for real-time frame risk assessment + optional object/region detection using Google Gemini (Generative AI) with WebSocket camera streaming and an image gallery.

---

## ✨ Features

- **Live Risk Monitoring** – Homepage auto connects to camera stream (or WebSocket sender) and periodically assesses frames.
- **Object / Region Detection** – Bounding box annotation via Gemini vision + `supervision` for overlay rendering.
- **Risk Assessment API** – Returns normalized score (0–1) + textual indicators (if present).
- **Gallery** – Stores risk flagged frames with JSON metadata (score, indicators, timestamp).
- **Real-time Alerts** – Audio + visual flashing border when threshold exceeded or indicators detected.
- **External WebSocket Camera Source** – `sender.py` publishes frames to all subscribers (multi-tab capable).
- **Optional Authentication** – Enable by setting `APP_USERNAME` + `APP_PASSWORD`.
- **Dark Mode UI** – Minimal, monitoring-friendly interface.
- **Exponential Backoff** – Automatic retry for transient Gemini overload / 5xx responses.

---

## 🧱 Architecture Overview

| Component | Purpose |
|-----------|---------|
| `app.py` | Flask + Socket.IO app, routes & REST APIs |
| `detector.py` | Gemini integration: detection, bounding boxes, risk scoring |
| `sender.py` | Stand-alone WebSocket frame broadcaster (camera capture) |
| `static/scan.js` | Frontend logic for live risk & box polling / streaming |
| `templates/` | Jinja2 HTML pages (layout, login, gallery, live scan) |
| `uploads/` | Raw user uploads (timestamped) |
| `annotated/` | AI annotated images |
| `gallery/` | Risk-flagged frames + per-image JSON metadata |

---

## 🔑 Environment Variables

| Name | Required | Description | Default |
|------|----------|-------------|---------|
| `GOOGLE_API_KEY` | Yes | Gemini API key | — |
| `MODEL_NAME` | No | Override model ID | `gemini-2.5-flash-preview-05-20` |
| `APP_USERNAME` | No | Enables auth (username) | — |
| `APP_PASSWORD` | No | Enables auth (password) | — |

Auth is disabled if either credential is missing.

---

## 🛠 Prerequisites

- Python 3.9+
- A Google Gemini API key from: https://aistudio.google.com/app/apikey

---

## 🚀 Installation & Setup

### 1. Clone
```bash
git clone <your-repo-url>
cd ZeroShotSucideDetection
```

### 2. Install dependencies
Using [uv](https://github.com/astral-sh/uv) (preferred):
```bash
uv sync
```
Or with pip:
```bash
pip install -r requirements.txt
```

### 3. Set environment variables
PowerShell (Windows):
```powershell
$env:GOOGLE_API_KEY="YOUR_KEY"
```
Unix shells:
```bash
export GOOGLE_API_KEY="YOUR_KEY"
```
Optional auth:
```powershell
$env:APP_USERNAME="admin"; $env:APP_PASSWORD="secret"
```

---

## ▶️ Running (Local Development)

### Option A: Built-in camera (browser getUserMedia)
Just start the Flask app; the live scan page will use the browser camera.
```bash
python app.py
```
Then open: http://127.0.0.1:5000/

### Option B: External WebSocket camera publisher
**Terminal 1 (frame broadcaster):**
```bash
python sender.py
```
**Terminal 2 (web app):**
```bash
python app.py
```
The live page subscribes to `ws://localhost:8765` and renders streamed frames.

---

## 📡 Live Monitoring Flow

1. Frame captured (browser or `sender.py`).
2. Frontend periodically sends frame (base64 JPEG) to `/api/risk_frame`.
3. Backend (`assess_risk`) sends resized image + JSON prompt to Gemini.
4. Response parsed: `{ score, indicators }` (score clamped 0–1).
5. UI updates; if `score >= threshold` or `indicators` non-empty ⇒ alert.
6. (Optional) Frame can also be saved + annotated via `/api/capture_and_save` or manual upload.

---

## 📁 File & Storage Behavior

| Directory | Purpose |
|-----------|---------|
| `uploads/` | Raw uploaded images (manual / API) |
| `annotated/` | Images with drawn boxes + labels |
| `gallery/` | Auto-saved risk frames + `<name>.json` metadata |

Annotated filename format: `<original_stem>_annotated<ext>`

---

## 🔌 API Endpoints (Summary)

| Method & Path | Purpose | Body | Returns |
|---------------|---------|------|---------|
| `POST /api/risk_frame` | Assess risk | `{ image }` | `{ score, indicators, timestamp }` |
| `POST /api/detect_frame` | Bounding boxes | `{ image, prompt? }` | `{ boxes, size }` |
| `POST /api/capture_and_save` | Store then annotate | `{ image, ... }` | `{ original, annotated? }` |
| `POST /api/upload_and_analyze` | Upload + risk | multipart `image` | `{ score, indicators, filename }` |
| `POST /upload` | Form upload & annotate | form-data `images[]` | Redirect + flash |
| `POST /delete` | Delete files | form `name` | Redirect + flash |

All APIs (except `/login`) require auth if configured.

---

## 🔁 Retry & Throttle Strategy

- `_generate_with_retry` uses exponential backoff for transient 5xx / overload errors.
- Frontend prevents overlapping in-flight requests per client.

---

## 🔐 Optional Authentication

Enabled when both `APP_USERNAME` and `APP_PASSWORD` are set. All primary routes then require login.

---

## 🛡 Security Notes

- Not production hardened (no CSRF, rate limiting, or MIME checks).
- Only extension filtering for uploads – add server-side validation before public exposure.
- Replace `SECRET_KEY` in `app.py` for any deployment.

---

## 🧭 Roadmap Ideas

- Drag & drop multi-upload UI
- Persistent user settings (thresholds, intervals)
- Async worker queue for annotation
- Model selection / prompt presets
- Enhanced gallery search/filter
- MIME type & size enforcement

---

## ⚖️ License
MIT

---

## 🙏 Acknowledgements
- Google Gemini for multimodal inference.
- Roboflow Supervision (`supervision`) for annotation utilities.

---

## ❗ Responsible Use Reminder
This is for experimentation with multimodal AI. Always involve qualified professionals for real mental health assessment.

---

### Quick Start (Copy/Paste)
```powershell
# Clone & enter
git clone <your-repo-url>
cd ZeroShotSucideDetection

# Install (uv)
uv sync

# Env vars
$env:GOOGLE_API_KEY="YOUR_KEY"

# Run app
python app.py

# (Optional) External publisher
python sender.py
```

Open http://127.0.0.1:5000 and observe live risk logs.

