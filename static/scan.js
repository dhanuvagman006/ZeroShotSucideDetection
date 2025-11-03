const imgEl = document.getElementById('scanVideo');
const startBtn = document.getElementById('scanStart');
const stopBtn = document.getElementById('scanStop');
const thresholdInput = document.getElementById('scanThreshold');
const autoStatusEl = document.getElementById('autoStatus');
const statusTextEl = document.getElementById('statusText');
const frameCountEl = document.getElementById('frameCount');
const lastCheckEl = document.getElementById('lastCheck');

let running = false;
let ws = null;
let frameCount = 0;
let intervalHandle = null;
let lastRawFrame = null;
let lastAnalyzedFrame = null;
let isAnalyzing = false;
const INTERNAL_PROMPT = "Analyze this image for signs of self-harm, suicide attempt, or suicidal ideation. Look for dangerous objects like knives, ropes, pills, self-inflicted injuries, distressed facial expressions indicating suicidal thoughts, or suicide notes/messages.";

function updateStatus(message, type = 'info') {
  if (statusTextEl) {
    statusTextEl.textContent = message;
  }
}

function updateFrameCount() {
  if (frameCountEl) {
    frameCountEl.textContent = frameCount;
  }
}

function updateLastCheck() {
  if (lastCheckEl) {
    const now = new Date().toLocaleTimeString();
    lastCheckEl.textContent = now;
  }
}

function updateAutoStatus(message, isError = false) {
  if (!autoStatusEl) return;
  autoStatusEl.textContent = message;
  
  autoStatusEl.classList.remove('success', 'error', 'warning');
  
  if (isError) {
    autoStatusEl.classList.add('error');
  } else if (message.includes('✅')) {
    autoStatusEl.classList.add('success');
  } else if (message.includes('🚨')) {
    autoStatusEl.classList.add('warning');
  }
}

async function connectWebSocket() {
  if (ws) return;
  try {
    updateAutoStatus('🔌 Connecting to camera stream...');
    updateStatus('Connecting to WebSocket...');
    const url = 'ws://localhost:8765';
    ws = new WebSocket(url);
    
    ws.onopen = () => {
      updateAutoStatus('✅ Connected - Monitoring active');
      updateStatus('Connected and monitoring');
    };
    
    ws.onmessage = (ev) => {
      lastRawFrame = ev.data;
      if (imgEl) {
        imgEl.src = 'data:image/jpeg;base64,' + lastRawFrame;
      }
    };
    
    ws.onerror = () => {
      updateAutoStatus('❌ Connection failed', true);
      updateStatus('WebSocket error');
    };
    
    ws.onclose = () => {
      updateAutoStatus('❌ Connection lost', true);
      updateStatus('Disconnected');
      ws = null;
    };
    
  } catch (e) {
    updateAutoStatus('❌ Failed to connect', true);
    updateStatus('Connection failed');
    throw e;
  }
}

function captureFrameDataURL() {
  if (!lastRawFrame) return null;
  return lastRawFrame.startsWith('data:') ? lastRawFrame : 'data:image/jpeg;base64,' + lastRawFrame;
}

async function captureAndAnalyze() {
  if (!running || isAnalyzing) return;
  
  const dataUrl = captureFrameDataURL();
  if (!dataUrl) {
    updateStatus('No frame available');
    return;
  }
  
  if (dataUrl === lastAnalyzedFrame) {
    updateStatus('Frame unchanged, skipping analysis');
    return;
  }
  isAnalyzing = true;
  lastAnalyzedFrame = dataUrl;
  frameCount++;
  updateFrameCount();
  updateStatus('Analyzing frame...');
  
  try {
    const res = await fetch('/api/risk_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        image: dataUrl,
        prompt: INTERNAL_PROMPT 
      })
    });
    
    const json = await res.json();
    
    if (json && !json.error) {
      const score = Number(json.score || 0);
      const indicators = json.indicators || [];
      const threshold = Number(thresholdInput.value || 0.5);
      
      updateLastCheck();
      
      if (score >= threshold || (indicators && indicators.length > 0)) {
        beep();
        updateAutoStatus(`🚨 RISK DETECTED - Score: ${score.toFixed(3)}`, true);
        updateStatus('⚠️ Risk detected!');
        await saveRiskFrame(dataUrl, json);
        const videoWrapper = imgEl.closest('.video-wrapper');
        if (videoWrapper) {
          videoWrapper.classList.add('risk-detected');
          setTimeout(() => {
            videoWrapper.classList.remove('risk-detected');
          }, 3000);
        }
      } else {
        updateStatus('✅ No risk detected');
        if (autoStatusEl && !autoStatusEl.textContent.includes('RISK')) {
          updateAutoStatus('✅ Monitoring - All clear');
        }
      }
    } else {
      updateStatus('❌ Analysis failed');
    }
  } catch (e) {
    updateStatus('❌ Network error');
  } finally {
    isAnalyzing = false;
  }
}

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    
    const createTone = (frequency, startTime, duration) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'square';
      osc.frequency.value = frequency;
      
      gain.gain.setValueAtTime(0.001, startTime);
      gain.gain.exponentialRampToValueAtTime(0.6, startTime + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
      
      osc.connect(gain).connect(ctx.destination);
      osc.start(startTime);
      osc.stop(startTime + duration);
    };
    const baseTime = ctx.currentTime;
    createTone(1000, baseTime, 0.2);
    createTone(1200, baseTime + 0.25, 0.2);
    createTone(1400, baseTime + 0.5, 0.3);
    
  } catch (e) {
    console.warn('Beep failed', e);
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'square';
      osc.frequency.value = 1000;
      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.5, ctx.currentTime + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.6);
    } catch (e2) {
      console.warn('Fallback beep also failed', e2);
    }
  }
}

async function startContinuousDetection() {
  if (running) return;
  
  try {
    await connectWebSocket();
    running = true;
    frameCount = 0;
    isAnalyzing = false;
    lastAnalyzedFrame = null;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    
    updateStatus('Starting monitoring...');
    updateFrameCount();
    setTimeout(captureAndAnalyze, 1000);
    intervalHandle = setInterval(captureAndAnalyze, 3000);
    
  } catch (e) {
    updateStatus('Failed to start');
    updateAutoStatus('❌ Failed to start monitoring', true);
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
}

function stopDetection() {
  if (!running) return;
  
  running = false;
  clearInterval(intervalHandle);
  intervalHandle = null;
  
  startBtn.disabled = false;
  stopBtn.disabled = true;
  
  updateStatus('Monitoring stopped');
  updateAutoStatus('🛑 Monitoring stopped');
  
  if (ws) {
    ws.close();
    ws = null;
  }
  
  isAnalyzing = false;
  lastAnalyzedFrame = null;
}

startBtn.addEventListener('click', startContinuousDetection);
stopBtn.addEventListener('click', stopDetection);

async function saveRiskFrame(imageDataUrl, analysisResult) {
  try {
    const metadata = {
      timestamp: analysisResult.timestamp || new Date().toISOString(),
      score: analysisResult.score || 0,
      indicators: analysisResult.indicators || [],
      source: 'monitoring'
    };
    
    const response = await fetch('/api/capture_and_save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        image: imageDataUrl,
        run_detection: false,
        save_to_gallery: true,
        metadata: metadata
      })
    });
    
    const result = await response.json();
    if (result.error) {
      console.warn('Failed to save risk frame:', result.error);
      return;
    }
    
    console.log('Risk frame saved to gallery:', result.original);
    
  } catch (e) {
    console.warn('Error saving risk frame:', e);
  }
}

window.addEventListener('load', () => {
  updateStatus('Initializing...');
  startBtn.disabled = false;
  stopBtn.disabled = true;
  setTimeout(startContinuousDetection, 2000);
});

window.addEventListener('beforeunload', () => {
  if (ws) {
    ws.close();
  }
});
