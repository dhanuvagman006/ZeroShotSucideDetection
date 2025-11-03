const fileInput = document.getElementById('customImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const uploadStatus = document.getElementById('uploadStatus');
const analysisResult = document.getElementById('analysisResult');
const analyzedImage = document.getElementById('analyzedImage');
const riskScore = document.getElementById('riskScore');
const riskIndicators = document.getElementById('riskIndicators');
const riskStatus = document.getElementById('riskStatus');
fileInput.addEventListener('change', () => {
  analyzeBtn.disabled = !fileInput.files.length;
  hideAnalysisResult();
});
analyzeBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) return;
  
  setUploadStatus('📤 Uploading and analyzing...', 'info');
  analyzeBtn.disabled = true;
  
  try {
    const formData = new FormData();
    formData.append('image', file);
    
    const response = await fetch('/api/upload_and_analyze', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.error) {
      setUploadStatus(`❌ Error: ${result.error}`, 'error');
      return;
    }
    
    showAnalysisResult(result, file);
    setUploadStatus('✅ Analysis complete!', 'success');
    if (result.score >= 0.5 || (result.indicators && result.indicators.length > 0)) {
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    }
    
  } catch (error) {
    setUploadStatus(`❌ Network error: ${error.message}`, 'error');
  } finally {
    analyzeBtn.disabled = false;
  }
});

function setUploadStatus(message, type) {
  uploadStatus.textContent = message;
  uploadStatus.className = `status-message ${type}`;
}

function showAnalysisResult(result, file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    analyzedImage.src = e.target.result;
  };
  reader.readAsDataURL(file);
  
  const score = result.score || 0;
  const indicators = result.indicators || [];
  
  riskScore.textContent = score.toFixed(3);
  
  if (indicators.length > 0) {
    riskIndicators.innerHTML = indicators.map(indicator => 
      `<span class="indicator-tag">${indicator}</span>`
    ).join('');
  } else {
    riskIndicators.textContent = 'None detected';
  }
  
  if (score >= 0.5 || indicators.length > 0) {
    riskStatus.textContent = '🚨 HIGH RISK';
    riskStatus.className = 'status-badge risk-high';
  } else if (score >= 0.3) {
    riskStatus.textContent = '⚠️ MODERATE RISK';
    riskStatus.className = 'status-badge risk-medium';
  } else {
    riskStatus.textContent = '✅ LOW RISK';
    riskStatus.className = 'status-badge risk-low';
  }
  
  analysisResult.style.display = 'block';
  analysisResult.scrollIntoView({ behavior: 'smooth' });
}

function hideAnalysisResult() {
  analysisResult.style.display = 'none';
}
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('gallery-image')) {
    showImageModal(e.target.src);
  }
});

function showImageModal(imageSrc) {
  const modal = document.createElement('div');
  modal.className = 'image-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <span class="close-modal">&times;</span>
      <img src="${imageSrc}" alt="Full size image" class="modal-image">
    </div>
  `;
  
  document.body.appendChild(modal);
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal || e.target.classList.contains('close-modal')) {
      document.body.removeChild(modal);
    }
  });
  
  document.addEventListener('keydown', function escapeHandler(e) {
    if (e.key === 'Escape') {
      if (document.body.contains(modal)) {
        document.body.removeChild(modal);
      }
      document.removeEventListener('keydown', escapeHandler);
    }
  });
}
setInterval(() => {
  if (!analyzeBtn.disabled && !analysisResult.style.display !== 'none') {
    window.location.reload();
  }
}, 30000);