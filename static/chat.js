/**
 * 上古必斩必杀 聊天功能
 */

async function newChat() {
  try {
    const res = await fetch(`${API}/api/new`, { method: 'POST' });
    const data = await res.json();
    threadId = data.thread_id;
    $threadBadge.textContent = threadId.slice(0, 8);
    $messages.innerHTML = `
      <div class="empty-state" id="empty-state">
        <div class="empty-state-title">上古必斩必杀</div>
        <div class="empty-state-sub">send a message to begin</div>
      </div>
    `;
    return data;
  } catch (e) {
    console.error('Failed to create new chat:', e);
  }
}

async function sendMessage(text) {
  if (!text.trim()) return;
  
  setBusyState(true);
  renderLoadingMessage();
  setLoading(true, 'processing');
  
  const previousMessages = $messages.querySelectorAll('.msg');
  let hasAssistant = false;
  previousMessages.forEach(msg => {
    if (msg.classList.contains('assistant')) hasAssistant = true;
  });
  
  renderMessage('user', text);
  
  try {
    const controller = new AbortController();
    currentAbortController = controller;
    
    const response = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, thread_id: threadId }),
      signal: controller.signal,
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let messageContent = '';
    let metadata = null;
    let loadingDiv = null;
    
    removeLoadingMessage();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            
            if (event.type === 'thread_id') {
              threadId = event.thread_id;
              $threadBadge.textContent = threadId.slice(0, 8);
            } else if (event.type === 'status') {
              if (!$messages.querySelector('.msg.assistant')) {
                renderLoadingMessage();
              }
              appendProgressMessage(event.message, 'info');
            } else if (event.type === 'todo_created') {
              appendProgressMessage('任务清单已创建', 'success');
              setTimeout(loadTodo, 500);
            } else if (event.type === 'tool_call') {
              appendProgressMessage(`[工具] ${event.name}: ${event.status}`, 'info');
            } else if (event.type === 'tool_calls') {
              appendProgressMessage(`[工具] ${event.tools.map(t => t.name).join(', ')}`, 'info');
            } else if (event.type === 'response') {
              messageContent += event.content;
              const lastMsg = $messages.querySelector('.msg.assistant:last-child');
              if (lastMsg) {
                lastMsg.querySelector('.msg-body').innerHTML = marked.parse(messageContent);
                lastMsg.querySelectorAll('pre code').forEach(block => {
                  hljs.highlightElement(block);
                });
              }
            } else if (event.type === 'done') {
              metadata = event.metadata;
            }
          } catch (e) {}
        }
      }
    }
    
    if (messageContent) {
      renderMessage('assistant', messageContent, metadata);
    }
    
  } catch (e) {
    if (e.name === 'AbortError') {
      appendProgressMessage('已中断', 'warning');
    } else {
      console.error('Chat error:', e);
      appendProgressMessage(`错误: ${e.message}`, 'error');
    }
  } finally {
    setBusyState(false);
    setLoading(false);
    currentAbortController = null;
    
    if (pendingMessages.length > 0 && !busy) {
      const nextMsg = pendingMessages.shift();
      pendingQueue.classList.add('active');
      renderPendingList();
      await sendMessage(nextMsg);
    } else if (pendingMessages.length === 0) {
      pendingQueue.classList.remove('active');
    }
  }
}

function addPendingMessage(text) {
  pendingMessages.push(text);
  renderPendingList();
  pendingQueue.classList.add('active');
}

function renderPendingList() {
  $pendingList.innerHTML = pendingMessages.map((msg, i) => `
    <div class="pending-item" data-index="${i}">
      <span class="pending-text">${escapeHtml(msg)}</span>
      <button class="pending-remove" data-index="${i}">×</button>
    </div>
  `).join('');
  
  $pendingList.querySelectorAll('.pending-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const index = parseInt(e.target.dataset.index);
      pendingMessages.splice(index, 1);
      renderPendingList();
      if (pendingMessages.length === 0) {
        pendingQueue.classList.remove('active');
      }
    });
  });
}

function clearPendingQueue() {
  pendingMessages = [];
  pendingQueue.classList.remove('active');
}