const statusEl = document.getElementById('rtStatus');
const imgEl = document.getElementById('rtFrame');
const btnConnect = document.getElementById('rtConnect');
const btnDisconnect = document.getElementById('rtDisconnect');
const btnStartDisplay = document.getElementById('rtStartDisplay');
const btnStopDisplay = document.getElementById('rtStopDisplay');

let ws = null;             // websocket instance
let frames = 0;            // displayed frames count
let startTime = null;      // display start time
let lastRawFrame = null;   // latest received base64 JPEG
let displaying = false;    // whether we are actively updating <img>
let animHandle = null;     // requestAnimationFrame id

function refreshButtons() {
  const connected = ws && ws.readyState === WebSocket.OPEN;
  // Connect button visible only when not connected
  btnConnect.classList.toggle('hidden', connected);
  // Disconnect visible only when connected
  btnDisconnect.classList.toggle('hidden', !connected);
  // Start Display visible when connected & not displaying
  btnStartDisplay.classList.toggle('hidden', !connected || displaying);
  btnStopDisplay.classList.toggle('hidden', !connected || !displaying);
  // Disable states
  btnDisconnect.disabled = !connected;
  btnStartDisplay.disabled = !connected || displaying;
  btnStopDisplay.disabled = !connected || !displaying;
}

function updateStatus(extra='') {
  if (!startTime || !displaying) {
    statusEl.textContent = `Frames: ${frames} ${extra}`;
    return;
  }
  const elapsed = (performance.now() - startTime)/1000;
  const fps = frames/elapsed;
  statusEl.textContent = `Frames: ${frames} | Avg FPS: ${fps.toFixed(2)} ${extra}`;
}

function connect() {
  if (ws) return;
  const url = 'ws://localhost:8765';
  statusEl.textContent = 'Connecting to ' + url + ' ...';
  try {
    ws = new WebSocket(url);
  } catch(e) {
    statusEl.textContent = 'WebSocket init failed: ' + e.message;
    return;
  }
  ws.onopen = () => {
    statusEl.textContent = 'Connected (not displaying yet)';
    refreshButtons();
  };
  ws.onmessage = (ev) => {
    lastRawFrame = ev.data; // base64 string
    if (!displaying) return; // store only
  };
  ws.onerror = () => {
    updateStatus(' | Error');
  };
  ws.onclose = () => {
    updateStatus(' | Closed');
    stopDisplay(true);
    ws = null;
    refreshButtons();
  };
}

function disconnect() { if (ws) ws.close(); }

function renderLoop() {
  if (!displaying) return;
  if (lastRawFrame) {
    imgEl.src = 'data:image/jpeg;base64,' + lastRawFrame;
    frames += 1;
    if (frames % 15 === 0) updateStatus();
  }
  animHandle = requestAnimationFrame(renderLoop);
}

function startDisplay() {
  if (!ws || ws.readyState !== WebSocket.OPEN || displaying) return;
  displaying = true;
  frames = 0;
  startTime = performance.now();
  updateStatus('(displaying)');
  refreshButtons();
  renderLoop();
}

function stopDisplay(fromClose=false) {
  if (!displaying && !fromClose) return;
  displaying = false;
  if (animHandle) cancelAnimationFrame(animHandle);
  if (!fromClose) updateStatus('(stopped)');
  refreshButtons();
}

btnConnect.addEventListener('click', connect);
btnDisconnect.addEventListener('click', disconnect);
btnStartDisplay.addEventListener('click', startDisplay);
btnStopDisplay.addEventListener('click', stopDisplay);

// Initial state
refreshButtons();
