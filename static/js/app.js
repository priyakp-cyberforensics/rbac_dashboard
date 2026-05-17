// Function to update the UI with new counts
function updateUICounters(allowed, denied) {
  const allowedCounters = document.querySelectorAll('.allowed-count');
  const deniedCounters = document.querySelectorAll('.denied-count');
  
  allowedCounters.forEach(counter => counter.textContent = allowed);
  deniedCounters.forEach(counter => counter.textContent = denied);
  
  // Update the chart if it exists
  const chartCanvas = document.getElementById('accessChart');
  if (chartCanvas && window.myChart) {
    window.myChart.data.datasets[0].data = [allowed, denied];
    window.myChart.update();
  }
}

// Function to fetch and update stats
async function fetchAndUpdateStats() {
  try {
    const response = await fetch('/stats.json');
    const data = await response.json();
    updateUICounters(data.allowed, data.denied);
    return data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    return { allowed: 0, denied: 0 };
  }
}

// Initialize refresh button functionality
document.addEventListener('DOMContentLoaded', function() {
  const refreshBtn = document.getElementById('refreshBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async function() {
      // Disable the button to prevent multiple clicks
      refreshBtn.disabled = true;
      
      // Show progress bar overlay
      const progressOverlay = document.createElement('div');
      progressOverlay.className = 'progress-overlay';
      progressOverlay.innerHTML = `
        <div class="progress-container">
          <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
          </div>
          <div class="progress-text">Resetting counters...</div>
        </div>
      `;
      
      // Style the progress overlay
      const style = document.createElement('style');
      style.textContent = `
        .progress-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: rgba(13, 17, 23, 0.9);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 9999;
        }
        .progress-container {
          width: 80%;
          max-width: 400px;
          text-align: center;
        }
        .progress {
          height: 20px;
          background-color: #0d1117;
          border: 1px solid #00adff;
          border-radius: 10px;
          overflow: hidden;
          margin-bottom: 10px;
        }
        .progress-bar {
          height: 100%;
          background: linear-gradient(90deg, #00adff, #00ffad);
          width: 0%;
          transition: width 0.5s ease-in-out;
        }
        .progress-text {
          color: #00adff;
          font-size: 1.2rem;
          text-shadow: 0 0 10px rgba(0, 173, 255, 0.5);
        }
      `;
      document.head.appendChild(style);
      document.body.appendChild(progressOverlay);
      
      // Animate progress bar
      const progressBar = progressOverlay.querySelector('.progress-bar');
      let progress = 0;
      const interval = setInterval(updateProgress, 30);
      
      function updateProgress() {
        progress += 2;
        if (progress <= 100) {
          progressBar.style.width = `${progress}%`;
        } else {
          clearInterval(interval);
          resetCounters();
        }
      }
      
      // Function to reset counters via API
      async function resetCounters() {
        try {
          // Call the reset endpoint
          const response = await fetch('/reset-counters', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          const result = await response.json();
          
          if (result.status === 'success') {
            // Update the UI with zeros
            updateUICounters(0, 0);
            
            // Update the progress text
            const progressText = progressOverlay.querySelector('.progress-text');
            if (progressText) {
              progressText.textContent = 'Counters reset successfully!';
            }
            
            // Close the overlay after a short delay
            setTimeout(() => {
              document.body.removeChild(progressOverlay);
              refreshBtn.disabled = false;
            }, 1000);
            
          } else {
            throw new Error(result.message || 'Failed to reset counters');
          }
        } catch (error) {
          console.error('Error resetting counters:', error);
          const progressText = progressOverlay.querySelector('.progress-text');
          if (progressText) {
            progressText.textContent = 'Error: ' + (error.message || 'Failed to reset counters');
            progressText.style.color = '#ff6b6b';
          }
          refreshBtn.disabled = false;
        }
      }
      
      // Add rotation animation to refresh button
      const icon = refreshBtn.querySelector('i');
      if (icon) {
        icon.style.transition = 'transform 1s ease-in-out';
        icon.style.transform = 'rotate(360deg)';
        
        // Reset rotation after animation completes
        setTimeout(() => {
          icon.style.transform = 'rotate(0deg)';
        }, 1000);
      }
    });
    
    // Initial fetch of stats
    fetchAndUpdateStats();
  }
});

// Chart rendering function
function renderAllowedDenied(canvasId, allowed, denied) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Allowed', 'Denied'],
      datasets: [{
        label: 'Decisions',
        data: [allowed, denied],
        backgroundColor: ['rgba(26,255,128,0.6)', 'rgba(255,59,59,0.6)'],
        borderColor: ['rgba(26,255,128,1)', 'rgba(255,59,59,1)'],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#a8b5d1' } },
        y: { grid: { color: '#24304d' }, ticks: { color: '#a8b5d1', stepSize: 1 } }
      }
    }
  });
}
