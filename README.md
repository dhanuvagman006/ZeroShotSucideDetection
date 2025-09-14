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
# Zero‑Shot Suicidal Risk Detection (Web App)

> Lightweight Flask application for real‑time frame risk assessment + optional object / region detection using Google Gemini (Generative AI) with WebSocket camera streaming and an image gallery.

⚠️ **Important Disclaimer**
This project is a **technical demo**. It is **NOT** a medical, psychological, or emergency tool and must **not** be relied upon for any clinical or life‑critical decision. If you or someone else is in immediate danger, contact your local emergency services or a suicide prevention hotline.

---

## ✨ Features

- **Live Risk Monitoring** – Homepage auto connects to camera stream (or WebSocket sender) and periodically assesses frames.
- **Object / Region Detection** – Bounding box annotation via Gemini vision + `supervision` for overlay rendering.
- **Risk Assessment API** – Returns normalized score (0–1) + textual indicators (if present).
- **Gallery** – Stores risk flagged frames with JSON metadata (score, indicators, timestamp).
- **Real‑time Alerts** – Audio + visual flashing border when threshold exceeded or indicators detected.
- **External WebSocket Camera Source** – `sender.py` publishes frames to all subscribers (multi‑tab capable).
- **Optional Authentication** – Enable by setting `APP_USERNAME` + `APP_PASSWORD`.
- **Dark Mode UI** – Minimal, monitoring‑friendly interface.
- **Exponential Backoff** – Automatic retry for transient Gemini overload / 5xx responses.

---

## 🧱 Architecture Overview

| Component | Purpose |
|-----------|---------|
| `app.py` | Flask + Socket.IO app, routes & REST APIs |
| `detector.py` | Gemini integration: detection, bounding boxes, risk scoring |
| `sender.py` | Stand‑alone WebSocket frame broadcaster (camera capture) |
| `static/scan.js` | Frontend logic for live risk & box polling / streaming |
| `templates/` | Jinja2 HTML pages (layout, login, gallery, live scan) |
| `uploads/` | Raw user uploads (timestamped) |
| `annotated/` | AI annotated ( *_annotated ) images |
| `gallery/` | Risk‑flagged frames + per‑image JSON metadata |

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

### Option A: Built‑in camera (browser getUserMedia)
Just start the Flask app; the live scan page will use the browser camera.
```bash
python app.py
```
Then open: http://127.0.0.1:5000/

### Option B: External WebSocket camera publisher
Terminal 1 (frame broadcaster):
```bash
python sender.py
```
Terminal 2 (web app):
```bash
python app.py
```
The live page subscribes to `ws://localhost:8765` and renders streamed frames.

---

## 📡 Live Monitoring Flow
1. Frame captured (browser or `sender.py`).
2. Frontend periodically (configurable interval) sends frame (base64 JPEG) to `/api/risk_frame`.
3. Backend (`assess_risk`) sends resized image + JSON‑contract prompt to Gemini.
4. Response parsed: `{ score, indicators }` (score clamped 0–1).
5. UI updates status log; if `score >= threshold` or `indicators` non‑empty ⇒ alert.
6. (Optional) Frame can also be saved + annotated via `/api/capture_and_save` or manual upload.

Bounding box detection uses a separate call (`detect_boxes` / `/api/detect_frame`) with a prompt suffix instructing Gemini to emit JSON bounding boxes.

---

## 📁 File & Storage Behavior
| Directory | Purpose |
|-----------|---------|
| `uploads/` | Raw uploaded images (manual / API) |
| `annotated/` | Images with drawn boxes + labels |
| `gallery/` | Auto‑saved risk frames + `<name>.json` metadata |
| `annotated/*.json` | (Not used currently – metadata only in `gallery/`) |

Annotated filename format: `<original_stem>_annotated<ext>`

---

## 🔌 API Endpoints (Summary)

| Method & Path | Purpose | Body (JSON/Form) | Returns |
|---------------|---------|------------------|---------|
| `POST /api/risk_frame` | Assess single frame risk | `{ image: <b64|dataURL> }` | `{ score, indicators, timestamp }` |
| `POST /api/detect_frame` | Bounding boxes | `{ image, prompt? }` | `{ boxes:[{box_2d,label}], size:[w,h] }` |
| `POST /api/capture_and_save` | Store frame + optional annotate | `{ image, prompt?, run_detection?, save_to_gallery?, metadata? }` | `{ original, annotated? }` |
| `POST /api/upload_and_analyze` | Upload file + risk | multipart `image` | `{ score, indicators, filename }` |
| `POST /upload` | (Form) batch upload + optional annotate | form-data `images[]` | Redirect + flash |
| `POST /delete` | Delete uploaded + annotated pair | form `name` | Redirect + flash |

All APIs (except `/login`) require auth if credentials are configured.

---

## 🧪 Risk Scoring Logic
Prompt instructs the model to output strictly:
```json
{ "score": <0..1>, "indicators": ["short", "keywords"] }
```
Soft‑fails: if parsing fails or model unavailable ⇒ `{ score: 0, indicators: [] }`.

---

## 🔁 Retry / Throttle Strategy
- `_generate_with_retry` backs off exponentially (up to 4 retries) for `503`, `500`, `UNAVAILABLE`, or "overloaded" responses.
- Frontend prevents overlapping in‑flight detection per client.

---

## 🔐 Optional Authentication
Enabled when both `APP_USERNAME` and `APP_PASSWORD` are set. All primary routes then require a session login. Logout clears `session['auth']`.

---

## 🛡 Security Notes
- Not production hardened (no rate limiting, CSRF protection, or MIME type verification).
- Only extension filtering for uploads – add server‑side MIME / size validation before production exposure.
- Never store real sensitive or private camera feeds without consent & encryption.
- Replace `SECRET_KEY` in `app.py` for any deployment.

---

## 🧭 Roadmap Ideas
- Drag & drop multi‑upload UI
- Persistent configuration (thresholds, intervals) per user
- Async worker queue for heavy annotation
- Model selection dropdown / multi‑prompt presets
- Better gallery filtering & search
- MIME type + size enforcement

---

## 🧪 Development Tips
- Use smaller frame intervals cautiously (cost & rate limits).
- Run `sender.py` separately to test multi‑subscriber frame distribution.
- Add logging around `_generate_with_retry` to tune latency vs reliability.

---

## 📦 Minimal Dependency List
See `requirements.txt` / `pyproject.toml`:
`flask`, `flask-socketio`, `pillow`, `google-genai`, `supervision`, `python-dotenv` (optional).

---

## ⚖️ License
MIT

---

## 🙏 Acknowledgements
- Google Gemini for multimodal inference.
- Roboflow Supervision (`supervision`) for annotation utilities.

---

## ❗ Responsible Use Reminder
This repository exists for experimentation with multimodal model integration. Always involve qualified professionals for real mental health assessment. Provide clear user warnings and obtain appropriate consent when capturing or analyzing images.

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

# Run
python app.py

# (Optional) External publisher
python sender.py
```

Open http://127.0.0.1:5000 and observe live risk logs.

---

Feel free to submit improvements or open issues for bugs / enhancement ideas.

