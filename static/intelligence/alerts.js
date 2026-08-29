/**
 * 上古必斩必杀 告警功能
 */

async function loadAlerts() {
  try {
    const res = await fetch(`${API}/api/alerts`);
    const data = await res.json();
    
    if (!data.alerts || data.alerts.length === 0) {
      $alertsList.innerHTML = '<div class="alert-empty">no alerts</div>';
      return;
    }
    
    $alertsList.innerHTML = data.alerts.map(alert => `
      <div class="alert-item ${alert.enabled ? '' : 'disabled'}" data-id="${alert.id}">
        <span class="alert-keyword" data-keyword="${escapeHtml(alert.keyword)}">${escapeHtml(alert.keyword)}</span>
        <div class="alert-actions">
          <button class="alert-btn toggle" data-id="${alert.id}" title="${alert.enabled ? '禁用' : '启用'}">${alert.enabled ? 'ON' : 'OFF'}</button>
          <button class="alert-btn delete" data-id="${alert.id}" title="删除">DEL</button>
        </div>
      </div>
    `).join('');
    
    $alertsList.querySelectorAll('.alert-keyword').forEach(el => {
      el.addEventListener('click', () => {
        const keyword = el.dataset.keyword;
        window.open(`/alert?keyword=${encodeURIComponent(keyword)}`, '_blank');
      });
    });
    
    $alertsList.querySelectorAll('.alert-btn.toggle').forEach(el => {
      el.addEventListener('click', async (e) => {
        e.stopPropagation();
        const alertId = el.dataset.id;
        await toggleAlert(alertId);
      });
    });
    
    $alertsList.querySelectorAll('.alert-btn.delete').forEach(el => {
      el.addEventListener('click', async (e) => {
        e.stopPropagation();
        const alertId = el.dataset.id;
        await deleteAlert(alertId);
      });
    });
  } catch (e) {
    console.error('Failed to load alerts:', e);
    $alertsList.innerHTML = '<div class="alert-empty">load failed</div>';
  }
}

async function addAlert(keyword) {
  try {
    const res = await fetch(`${API}/api/alerts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword }),
    });
    
    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || '添加失败');
      return;
    }
    
    $alertInput.value = '';
    loadAlerts();
  } catch (e) {
    console.error('Failed to add alert:', e);
    alert('添加失败: ' + e.message);
  }
}

async function toggleAlert(alertId) {
  try {
    const res = await fetch(`${API}/api/alerts/${alertId}/toggle`, {
      method: 'POST',
    });
    
    if (res.ok) {
      loadAlerts();
    }
  } catch (e) {
    console.error('Failed to toggle alert:', e);
  }
}

async function deleteAlert(alertId) {
  try {
    const res = await fetch(`${API}/api/alerts/${alertId}`, {
      method: 'DELETE',
    });
    
    if (res.ok) {
      loadAlerts();
      loadAlertHistory();
    }
  } catch (e) {
    console.error('Failed to delete alert:', e);
  }
}

async function loadAlertHistory() {
  try {
    const res = await fetch(`${API}/api/alerts/history?limit=20`);
    const data = await res.json();
    
    if (!data.history || data.history.length === 0) {
      $alertHistoryList.innerHTML = '<div class="alert-empty-small">no history</div>';
      return;
    }
    
    $alertHistoryList.innerHTML = data.history.map(item => `
      <div class="alert-history-item" data-keyword="${escapeHtml(item.keyword)}">
        <div class="alert-keyword">${escapeHtml(item.keyword)}</div>
        <div class="alert-title">${escapeHtml(item.title)}</div>
        <div class="alert-meta">
          <span class="alert-source-tag">${escapeHtml(item.source || item.type)}</span>
          <span>${formatAlertTime(item.triggered_at)}</span>
        </div>
      </div>
    `).join('');
    
    $alertHistoryList.querySelectorAll('.alert-history-item').forEach(el => {
      el.addEventListener('click', () => {
        const keyword = el.dataset.keyword;
        window.open(`/alert?keyword=${encodeURIComponent(keyword)}`, '_blank');
      });
    });
  } catch (e) {
    console.error('Failed to load alert history:', e);
    $alertHistoryList.innerHTML = '<div class="alert-empty-small">load failed</div>';
  }
}

async function clearAlertHistory() {
  try {
    const res = await fetch(`${API}/api/alerts/history/all`, {
      method: 'DELETE',
    });
    
    if (res.ok) {
      loadAlertHistory();
    }
  } catch (e) {
    console.error('Failed to clear alert history:', e);
  }
}

function handleNewAlert(alertEvent) {
  appendProgressMessage(`[告警] ${alertEvent.keyword}: ${alertEvent.title}`, 'warning');
  loadAlertHistory();
  
  if ($alertsList.querySelector('.alert-empty')) {
    loadAlerts();
  }
}

function startAlertStream() {
  const eventSource = new EventSource(`${API}/api/alerts/stream`);
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'alert' && data.event) {
        const alertEvent = data.event;
        handleNewAlert(alertEvent);
      } else if (data.type === 'ping') {
        // heartbeat
      }
    } catch (e) {
      console.error('Failed to parse alert event:', e);
    }
  };
  
  eventSource.onerror = () => {
    console.log('Alert stream connection lost, reconnecting...');
    eventSource.close();
    setTimeout(startAlertStream, 5000);
  };
}