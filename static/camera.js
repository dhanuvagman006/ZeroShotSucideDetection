const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');
let running = false;
let lastTime = 0;
let detectionsCount = 0;
let fpsSamples = [];
let socket = null;
let fallbackTimer = null;

function resizeCanvas() {
  overlay.width = video.videoWidth;
  overlay.height = video.videoHeight;
}

async function initCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640 }, audio: false });
    video.srcObject = stream;
    await video.play();
    resizeCanvas();
  } catch (e) {
    statusEl.textContent = 'Camera error: ' + e.message;
  }
}

function grabFrame() {
  const c = document.createElement('canvas');
  c.width = video.videoWidth; c.height = video.videoHeight;
  const ctx = c.getContext('2d');
  ctx.drawImage(video, 0, 0);
  return c.toDataURL('image/jpeg', 0.8);
}

function drawBoxes(payload) {
  const ctx = overlay.getContext('2d');
  ctx.clearRect(0,0,overlay.width, overlay.height);
  const wScale = overlay.width / payload.size[0];
  const hScale = overlay.height / payload.size[1];
  ctx.lineWidth = 2; ctx.font = '12px system-ui'; ctx.strokeStyle = '#00ff57'; ctx.fillStyle = 'rgba(0,0,0,0.55)';
  for (const box of payload.boxes) {
    const [x1,y1,x2,y2] = box.box_2d;
    const rx1 = x1*wScale, ry1 = y1*hScale, rw=(x2-x1)*wScale, rh=(y2-y1)*hScale;
    ctx.strokeRect(rx1, ry1, rw, rh);
    const label = box.label || '';
    if (label) {
      const pad = 2;
      const tw = ctx.measureText(label).width;
      ctx.fillRect(rx1, ry1-14, tw+pad*2, 14);
      ctx.fillStyle = '#fff';
      ctx.fillText(label, rx1+pad, ry1-3);
      ctx.fillStyle = 'rgba(0,0,0,0.55)';
    }
  }
}

function updateFPS() {
  const now = performance.now();
  if (lastTime) {
    const delta = (now - lastTime) / 1000;
    const fps = 1 / delta;
    fpsSamples.push(fps);
    if (fpsSamples.length > 20) fpsSamples.shift();
    const avg = fpsSamples.reduce((a,b)=>a+b,0)/fpsSamples.length;
    statusEl.textContent = `Boxes: ${detectionsCount} | Avg FPS: ${avg.toFixed(2)}`;
  }
  lastTime = now;
}

function startWS() {
  if (!window.io) return false;
  socket = io();
  socket.on('connect', () => { statusEl.textContent = 'WS connected'; });
  socket.on('boxes', data => {
    detectionsCount = data.boxes.length;
    drawBoxes(data);
    updateFPS();
    if (running) sendFrameWS();
  });
  socket.on('error', e => { statusEl.textContent = 'Error: ' + (e.error || 'unknown'); });
  return true;
}

function sendFrameWS() {
  if (!socket || socket.disconnected) return;
  const frame = grabFrame();
  const prompt = document.getElementById('prompt').value.trim();
  socket.emit('frame', { image: frame, prompt });
}

async function fallbackLoop() {
  if (!running) return;
  const frame = grabFrame();
  const prompt = document.getElementById('prompt').value.trim();
  try {
    const res = await fetch('/api/detect_frame', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ image: frame, prompt })});
    const json = await res.json();
    if (!json.error) {
      detectionsCount = json.boxes.length;
      drawBoxes(json);
      updateFPS();
    } else {
      statusEl.textContent = 'Error: ' + json.error;
    }
  } catch (e) {
    statusEl.textContent = 'Error: ' + e.message;
  }
  const interval = parseInt(document.getElementById('interval').value,10) || 1500;
  fallbackTimer = setTimeout(fallbackLoop, interval);
}

startBtn.addEventListener('click', () => {
  if (running) return;
  running = true;
  startBtn.disabled = true; stopBtn.disabled = false;
  if (!startWS()) {
    statusEl.textContent = 'Using HTTP fallback';
    fallbackLoop();
  } else {
    sendFrameWS();
  }
});

stopBtn.addEventListener('click', () => {
  running = false;
  startBtn.disabled = false; stopBtn.disabled = true;
  if (fallbackTimer) clearTimeout(fallbackTimer);
  statusEl.textContent = 'Stopped';
});

window.addEventListener('resize', resizeCanvas);
initCamera();
