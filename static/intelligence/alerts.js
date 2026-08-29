/**
 * 上古必斩必杀 告警功能
 */

// 未读告警计数与 SSE 连接状态
let alertUnreadCount = 0;          // 收到但尚未查看的新告警数
let alertStreamFirstOpen = true;   // SSE 首次连接标志(断线重连时补拉错过的数据)

function updateAlertUnread() {
  if (!$alertUnreadBadge) return;
  $alertUnreadBadge.hidden = alertUnreadCount <= 0;
  $alertUnreadBadge.textContent = alertUnreadCount > 99 ? '99+' : String(alertUnreadCount);
}

function clearAlertUnread() {
  alertUnreadCount = 0;
  updateAlertUnread();
}

/* ---- 规则列表 ---- */

function renderAlertItem(alert) {
  const count = alert.event_count != null ? alert.event_count : 0;
  const lastText = alert.last_triggered_at ? formatAlertTime(alert.last_triggered_at) : '从未触发';
  const toggleTitle = alert.enabled ? '禁用' : '启用';
  const toggleBtn = alert.enabled ? 'ON' : 'OFF';
  return (
    '<div class="alert-item ' + (alert.enabled ? '' : 'disabled') + '" data-id="' + alert.id + '" data-count="' + count + '" data-last="' + (alert.last_triggered_at || '') + '">' +
      '<div class="alert-main">' +
        '<span class="alert-keyword" data-keyword="' + escapeHtml(alert.keyword) + '">' + escapeHtml(alert.keyword) + '</span>' +
        '<div class="alert-item-stats">' +
          '<span class="alert-item-count">' + count + ' 次触发</span>' +
          '<span class="alert-item-last">' + escapeHtml(lastText) + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="alert-actions">' +
        '<button class="alert-btn toggle" title="' + toggleTitle + '">' + toggleBtn + '</button>' +
        '<button class="alert-btn delete" title="删除">DEL</button>' +
      '</div>' +
    '</div>'
  );
}

async function loadAlerts() {
  try {
    const res = await fetch(API + '/api/alerts');
    const data = await res.json();

    if (!data.alerts || data.alerts.length === 0) {
      $alertsList.innerHTML = '<div class="alert-empty">no alerts</div>';
      return;
    }

    $alertsList.innerHTML = data.alerts.map(renderAlertItem).join('');
  } catch (e) {
    console.error('Failed to load alerts:', e);
    $alertsList.innerHTML = '<div class="alert-empty">load failed</div>';
  }
}

// 规则列表事件委托:关键词→时间线、ON/OFF、DEL
$alertsList.addEventListener('click', (e) => {
  const item = e.target.closest('.alert-item');
  if (!item) return;

  if (e.target.classList.contains('alert-keyword')) {
    const keyword = e.target.dataset.keyword;
    window.open('/alert?keyword=' + encodeURIComponent(keyword), '_blank');
  } else if (e.target.classList.contains('toggle')) {
    toggleAlert(item.dataset.id);
  } else if (e.target.classList.contains('delete')) {
    deleteAlert(item.dataset.id);
  }
});

async function addAlert(keyword) {
  try {
    const res = await fetch(API + '/api/alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword }),
    });

    if (!res.ok) {
      let detail = '添加失败';
      try { detail = (await res.json()).detail || detail; } catch (e) {}
      alert(detail);
      return;
    }

    $alertInput.value = '';
    const data = await res.json();
    await loadAlerts();
    highlightAlertItem(data.alert && data.alert.id);
  } catch (e) {
    console.error('Failed to add alert:', e);
    alert('添加失败: ' + e.message);
  }
}

/** 高亮并滚动到指定规则(添加成功后定位反馈) */
function highlightAlertItem(alertId) {
  if (!alertId) return;
  const el = $alertsList.querySelector('.alert-item[data-id="' + alertId + '"]');
  if (!el) return;
  el.classList.remove('new');
  void el.offsetWidth; // 重启动画
  el.classList.add('new');
  el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

async function toggleAlert(alertId) {
  try {
    const res = await fetch(API + '/api/alerts/' + alertId + '/toggle', { method: 'POST' });
    if (res.ok) loadAlerts();
  } catch (e) {
    console.error('Failed to toggle alert:', e);
  }
}

async function deleteAlert(alertId) {
  try {
    const res = await fetch(API + '/api/alerts/' + alertId, { method: 'DELETE' });
    if (res.ok) {
      loadAlerts();
      loadAlertHistory();
      clearAlertUnread();
    }
  } catch (e) {
    console.error('Failed to delete alert:', e);
  }
}

/* ---- 告警历史 ---- */

function historyItemHtml(item) {
  return (
    '<div class="alert-history-item" data-keyword="' + escapeHtml(item.keyword) + '">' +
      '<div class="alert-keyword">' + escapeHtml(item.keyword) + '</div>' +
      '<div class="alert-title">' + escapeHtml(item.title) + '</div>' +
      '<div class="alert-meta">' +
        '<span class="alert-source-tag">' + escapeHtml(item.source || item.type) + '</span>' +
        '<span>' + formatAlertTime(item.triggered_at) + '</span>' +
      '</div>' +
    '</div>'
  );
}

async function loadAlertHistory() {
  try {
    const res = await fetch(API + '/api/alerts/history?limit=20');
    const data = await res.json();

    if (!data.history || data.history.length === 0) {
      $alertHistoryList.innerHTML = '<div class="alert-empty-small">no history</div>';
      return;
    }

    $alertHistoryList.innerHTML = data.history.map(historyItemHtml).join('');

    $alertHistoryList.querySelectorAll('.alert-history-item').forEach(el => {
      el.addEventListener('click', () => {
        const keyword = el.dataset.keyword;
        window.open('/alert?keyword=' + encodeURIComponent(keyword), '_blank');
      });
    });
  } catch (e) {
    console.error('Failed to load alert history:', e);
    $alertHistoryList.innerHTML = '<div class="alert-empty-small">load failed</div>';
  }
}

/** 本地插入一条新告警事件,避免每次告警都全量重拉历史 */
function prependAlertHistoryItem(event) {
  const emptyEl = $alertHistoryList.querySelector('.alert-empty-small');
  if (emptyEl) emptyEl.remove();

  const el = document.createElement('div');
  el.className = 'alert-history-item new';
  el.dataset.keyword = event.keyword || '';
  el.innerHTML = historyItemHtml(event);
  el.addEventListener('click', () => {
    const keyword = el.dataset.keyword;
    if (keyword) window.open('/alert?keyword=' + encodeURIComponent(keyword), '_blank');
  });
  $alertHistoryList.prepend(el);

  // 与后端 limit=20 保持一致
  while ($alertHistoryList.children.length > 20) {
    $alertHistoryList.lastElementChild.remove();
  }
}

/** 更新对应规则的本地计数与最后触发时间 */
function bumpAlertItemStats(alertId) {
  if (!alertId) return;
  const el = $alertsList.querySelector('.alert-item[data-id="' + alertId + '"]');
  if (!el) return;

  const count = (parseInt(el.dataset.count, 10) || 0) + 1;
  el.dataset.count = String(count);
  const countEl = el.querySelector('.alert-item-count');
  if (countEl) countEl.textContent = count + ' 次触发';
  const lastEl = el.querySelector('.alert-item-last');
  if (lastEl) lastEl.textContent = formatAlertTime(new Date().toISOString());

  el.classList.remove('new');
  void el.offsetWidth;
  el.classList.add('new');
}

async function clearAlertHistory() {
  try {
    const res = await fetch(API + '/api/alerts/history/all', { method: 'DELETE' });
    if (res.ok) loadAlertHistory();
  } catch (e) {
    console.error('Failed to clear alert history:', e);
  }
}

/* ---- SSE 实时推送 ---- */

// 节流:批量告警时合并为一次兜底全量刷新,本地渲染保持即时
let _historyRefreshTimer = null;

function handleNewAlert(alertEvent) {
  // 字段容错:事件结构不完整时仍给出可读提示,避免渲染 undefined
  const event = alertEvent || {};
  const kw = event.keyword || '(未知关键词)';
  const title = event.title || '(无标题)';
  appendProgressMessage('[告警] ' + kw + ': ' + title, 'warning');

  prependAlertHistoryItem(event);
  bumpAlertItemStats(event.alert_id);

  // 未读徽标:切到 ALERTS 标签页前持续累积
  alertUnreadCount += 1;
  updateAlertUnread();

  if (_historyRefreshTimer) clearTimeout(_historyRefreshTimer);
  _historyRefreshTimer = setTimeout(() => {
    loadAlertHistory();
    loadAlerts();
  }, 5000);
}

function startAlertStream() {
  const eventSource = new EventSource(API + '/api/alerts/stream');

  // 首次连接不重复加载;断线重连成功后补拉错过的告警与规则
  eventSource.onopen = () => {
    if (!alertStreamFirstOpen) {
      loadAlerts();
      loadAlertHistory();
    }
    alertStreamFirstOpen = false;
  };

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === 'alert' && data.event) {
        // 归一化:兼容历史上被二次包装的载荷(内层还带 event 时取内层真实事件)
        const payload = data.event.event ? data.event.event : data.event;
        handleNewAlert(payload);
      } else if (data.type === 'alert_updated') {
        // 其他标签页的规则增删改,同步本页规则列表
        loadAlerts();
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
