/**
 * 上古必斩必杀 历史记录功能
 */

async function loadHistory() {
  try {
    const res = await fetch(`${API}/api/history`);
    const data = await res.json();
    
    if (!data.history || data.history.length === 0) {
      $historyList.innerHTML = '<div class="history-empty">no history</div>';
      return;
    }
    
    $historyList.innerHTML = data.history.map(item => `
      <div class="history-item" data-thread="${item.thread_id}">
        <div class="history-id">${item.thread_id.slice(0, 8)}</div>
        <div class="history-preview">${escapeHtml(item.last_message || 'empty')}</div>
        <button class="history-delete" data-thread="${item.thread_id}">×</button>
      </div>
    `).join('');
    
    $historyList.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', async (e) => {
        if (e.target.classList.contains('history-delete')) return;
        const tid = el.dataset.thread;
        await loadHistoryThread(tid);
      });
    });
    
    $historyList.querySelectorAll('.history-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const tid = btn.dataset.thread;
        await deleteHistory(tid);
      });
    });
  } catch (e) {
    console.error('Failed to load history:', e);
    $historyList.innerHTML = '<div class="history-empty">load failed</div>';
  }
}

async function loadHistoryThread(threadId) {
  try {
    const res = await fetch(`${API}/api/history/${threadId}`);
    const data = await res.json();
    
    threadId = data.thread_id;
    $threadBadge.textContent = threadId.slice(0, 8);
    $messages.innerHTML = '';
    
    for (const msg of data.messages) {
      renderMessage(msg.role, msg.content, msg.metadata);
    }
  } catch (e) {
    console.error('Failed to load history thread:', e);
  }
}

async function deleteHistory(threadId) {
  try {
    await fetch(`${API}/api/history/${threadId}`, { method: 'DELETE' });
    loadHistory();
  } catch (e) {
    console.error('Failed to delete history:', e);
  }
}