// gallery.js - Gallery functionality for risk-detected frames and custom photo upload

const fileInput = document.getElementById('customImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const uploadStatus = document.getElementById('uploadStatus');
const analysisResult = document.getElementById('analysisResult');
const analyzedImage = document.getElementById('analyzedImage');
const riskScore = document.getElementById('riskScore');
const riskIndicators = document.getElementById('riskIndicators');
const riskStatus = document.getElementById('riskStatus');

// Enable analyze button when file is selected
fileInput.addEventListener('change', () => {
  analyzeBtn.disabled = !fileInput.files.length;
  hideAnalysisResult();
});

// Analyze uploaded image
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
    
    // Show analysis result
    showAnalysisResult(result, file);
    setUploadStatus('✅ Analysis complete!', 'success');
    
    // Auto refresh page after 3 seconds if risk was detected and saved to gallery
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
  // Display uploaded image
  const reader = new FileReader();
  reader.onload = (e) => {
    analyzedImage.src = e.target.result;
  };
  reader.readAsDataURL(file);
  
  // Display analysis results
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
  
  // Set risk status
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

// Add click handler for gallery images to show full size
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('gallery-image')) {
    showImageModal(e.target.src);
  }
});

function showImageModal(imageSrc) {
  // Create modal overlay
  const modal = document.createElement('div');
  modal.className = 'image-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <span class="close-modal">&times;</span>
      <img src="${imageSrc}" alt="Full size image" class="modal-image">
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Close modal when clicking overlay or close button
  modal.addEventListener('click', (e) => {
    if (e.target === modal || e.target.classList.contains('close-modal')) {
      document.body.removeChild(modal);
    }
  });
  
  // Close modal with Escape key
  document.addEventListener('keydown', function escapeHandler(e) {
    if (e.key === 'Escape') {
      if (document.body.contains(modal)) {
        document.body.removeChild(modal);
      }
      document.removeEventListener('keydown', escapeHandler);
    }
  });
}

// Auto-refresh gallery every 30 seconds to show new risk-detected frames
setInterval(() => {
  // Only refresh if no analysis is in progress
  if (!analyzeBtn.disabled && !analysisResult.style.display !== 'none') {
    window.location.reload();
  }
}, 30000);