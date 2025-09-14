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

