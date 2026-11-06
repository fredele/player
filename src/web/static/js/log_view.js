const logOutput = document.getElementById('log-output');
const statusEl = document.getElementById('status');
const linesInput = document.getElementById('log-lines');

function getToken() {
  return localStorage.getItem('token') || '';
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? '#ff8a8a' : '#bfc6d0';
}

async function fetchLog() {
  const lines = Math.max(50, Number(linesInput.value) || 200);
  const token = getToken();

  setStatus('Loading log…');
  logOutput.textContent = 'Loading log…';

  try {
    const response = await fetch(`/v1/Logs/Content?lines=${lines}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const payload = await response.json();

    if (!response.ok || payload.response === 'error') {
      throw new Error(payload.message || 'Unable to read the log file');
    }

    logOutput.textContent = payload.log || 'No log output to display.';
    setStatus(`Loaded ${payload.lines || 0} lines from ${payload.path || 'log file'}`);
  } catch (error) {
    logOutput.textContent = error.message || 'Unable to load the log.';
    setStatus(error.message || 'Error', true);
  }
}

linesInput.addEventListener('keydown', function (event) {
  if (event.key === 'Enter') {
    fetchLog();
  }
});

document.getElementById('refresh-log').addEventListener('click', fetchLog);
document.getElementById('download-log').addEventListener('click', async function () {
  const token = getToken();

  try {
    const response = await fetch('/v1/Logs/Download', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      throw new Error(payload?.message || 'Unable to download the log file');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'log.txt';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus('Log file downloaded');
  } catch (error) {
    setStatus(error.message || 'Unable to download the log file', true);
  }
});

fetchLog();
