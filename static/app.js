// ── config ──
const API = '';
const POLL_INTERVAL = 2000;

// ── state ──
let threadId = null;
let busy = false;
let pendingMessages = [];
let todoPollInterval = null;
let currentAbortController = null;

// ── dom ──
const $messages = document.getElementById('messages');
const $input = document.getElementById('msg-input');
const $send = document.getElementById('btn-send');
const $loading = document.getElementById('loading');
const $loadingText = document.getElementById('loading-text');
const $threadBadge = document.getElementById('thread-badge');
const $btnNew = document.getElementById('btn-new');
const $historyList = document.getElementById('history-list');
const $todoContent = document.getElementById('todo-content');
const $skillsList = document.getElementById('skills-list');
const $toolsList = document.getElementById('tools-list');
const $pendingQueue = document.getElementById('pending-queue');
const $pendingList = document.getElementById('pending-list');
const $btnClearPending = document.getElementById('btn-clear-pending');
const $btnRefreshHistory = document.getElementById('btn-refresh-history');
const $btnRefreshTodo = document.getElementById('btn-refresh-todo');

// ── marked config ──
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true,
  gfm: true,
});

// ── helpers ──
function scrollToBottom() {
  $messages.scrollTop = $messages.scrollHeight;
}

function setLoading(on, text) {
  $loading.classList.toggle('active', on);
  if (text) $loadingText.textContent = text;
}

function setBusy(on) {
  busy = on;
  $send.disabled = on;
}

function updateThread(id) {
  threadId = id;
  $threadBadge.textContent = id ? id.slice(0, 8) : '';
  startTodoPolling();
  loadHistory();
}

function removeEmptyState() {
  const el = document.getElementById('empty-state');
  if (el) el.remove();
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function renderMarkdown(text) {
  return marked.parse(text);
}

// ── render functions ──

function appendUserMessage(text) {
  removeEmptyState();
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `
    <div class="msg-role msg-role-user">YOU</div>
    <div class="msg-body">${escapeHtml(text)}</div>
  `;
  $messages.appendChild(el);
  scrollToBottom();
}

function appendAssistantMessage(html) {
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `
    <div class="msg-role">ASSISTANT</div>
    <div class="msg-body">${html}</div>
  `;
  $messages.appendChild(el);
  scrollToBottom();
}

function appendToolCalls(toolCalls) {
  if (!toolCalls || !toolCalls.length) return;
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `
    <div class="msg-role">TOOLS</div>
    ${toolCalls.map(tc => `<div class="tool-call">${escapeHtml(tc.name)}</div>`).join('')}
  `;
  $messages.appendChild(el);
  scrollToBottom();
}

function appendIterationBlock(label, content) {
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `
    <div class="iteration-block">
      <div class="iter-label">${label}</div>
      <div class="iter-content">${escapeHtml(content)}</div>
    </div>
  `;
  $messages.appendChild(el);
  scrollToBottom();
}

function appendSummary(content) {
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `<div class="summary-block">${renderMarkdown(content)}</div>`;
  $messages.appendChild(el);
  scrollToBottom();
}

function appendError(msg) {
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `
    <div class="msg-role">ERROR</div>
    <div class="msg-body" style="color:var(--fg-dim)">${escapeHtml(msg)}</div>
  `;
  $messages.appendChild(el);
  scrollToBottom();
}

// ── pending queue ──

function updatePendingQueue() {
  if (pendingMessages.length === 0) {
    $pendingQueue.style.display = 'none';
    $pendingList.innerHTML = '';
    return;
  }

  $pendingQueue.style.display = 'block';
  $pendingList.innerHTML = pendingMessages.map((msg, i) => `
    <div class="pending-item">${escapeHtml(msg)}</div>
  `).join('');
}

function addPendingMessage(text) {
  pendingMessages.push(text);
  updatePendingQueue();
}

function clearPendingQueue() {
  pendingMessages = [];
  updatePendingQueue();
}

async function sendPendingMessages() {
  const messages = [...pendingMessages];
  pendingMessages = [];
  updatePendingQueue();

  for (const msg of messages) {
    await sendMessage(msg);
  }
}

// ── history ──

async function loadHistory() {
  try {
    const res = await fetch(`${API}/api/history`);
    const data = await res.json();

    if (!data.history || data.history.length === 0) {
      $historyList.innerHTML = '<div class="history-empty">no history</div>';
      return;
    }

    $historyList.innerHTML = data.history.map(item => `
      <div class="history-item ${item.thread_id === threadId ? 'active' : ''}" data-thread="${item.thread_id}">
        <span class="history-item-delete" onclick="event.stopPropagation(); deleteHistory('${item.thread_id}')">DEL</span>
        <div class="history-item-thread">${item.thread_id.slice(0, 12)}...</div>
        <div class="history-item-preview">${escapeHtml(item.last_message || 'empty')}</div>
      </div>
    `).join('');

    $historyList.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', () => loadChatHistory(el.dataset.thread));
    });
  } catch (e) {
    console.error('Failed to load history:', e);
  }
}

async function loadChatHistory(tid) {
  try {
    const res = await fetch(`${API}/api/history/${tid}`);
    if (!res.ok) {
      appendError('Failed to load chat history');
      return;
    }

    const data = await res.json();
    updateThread(tid);

    $messages.innerHTML = '';
    if (data.messages && data.messages.length > 0) {
      data.messages.forEach(msg => {
        if (msg.role === 'user') {
          const el = document.createElement('div');
          el.className = 'msg';
          el.innerHTML = `
            <div class="msg-role msg-role_user">YOU</div>
            <div class="msg-body">${escapeHtml(msg.content)}</div>
          `;
          $messages.appendChild(el);
        } else if (msg.role === 'assistant') {
          const el = document.createElement('div');
          el.className = 'msg';
          el.innerHTML = `
            <div class="msg-role">ASSISTANT</div>
            <div class="msg-body">${renderMarkdown(msg.content)}</div>
          `;
          $messages.appendChild(el);
        }
      });
    } else {
      const empty = document.createElement('div');
      empty.className = 'empty-state';
      empty.id = 'empty-state';
      empty.innerHTML = `
        <div class="empty-state-title">onekiil4all</div>
        <div class="empty-state-sub">send a message to begin</div>
      `;
      $messages.appendChild(empty);
    }
    scrollToBottom();
    loadHistory();
  } catch (e) {
    appendError(e.message);
  }
}

async function deleteHistory(tid) {
  try {
    await fetch(`${API}/api/history/${tid}`, { method: 'DELETE' });
    loadHistory();
    if (tid === threadId) {
      newChat();
    }
  } catch (e) {
    console.error('Failed to delete history:', e);
  }
}

// ── todo ──

async function loadTodo() {
  if (!threadId) return;

  try {
    const res = await fetch(`${API}/api/todo?thread_id=${threadId}`);
    const data = await res.json();

    if (!data.exists || !data.tasks || data.tasks.length === 0) {
      // 只有在没有显示内容时才显示"no active task"
      if (!$todoContent.querySelector('.todo-block') && !$todoContent.querySelector('.todo-item')) {
        $todoContent.innerHTML = '<div class="todo-empty">no active task</div>';
      }
      return;
    }

    const pct = data.total_count ? Math.round((data.completed_count / data.total_count) * 100) : 0;
    $todoContent.innerHTML = `
      <div class="todo-block">
        <div class="todo-header">
          <span>TODO ${data.completed_count}/${data.total_count}</span>
          <div class="todo-progress-bar">
            <div class="todo-progress-fill" style="width:${pct}%"></div>
          </div>
        </div>
        ${data.tasks.map(t => `
          <div class="todo-item ${t.completed ? 'completed' : ''}">
            <div class="todo-check"><div class="todo-check-inner"></div></div>
            <span>${escapeHtml(t.description)}</span>
          </div>
        `).join('')}
      </div>
    `;
  } catch (e) {
    console.error('Failed to load todo:', e);
  }
}

function updateTodoDisplay(todo) {
  console.log('updateTodoDisplay called with:', todo);
  if (!todo || !todo.tasks || todo.tasks.length === 0) {
    $todoContent.innerHTML = '<div class="todo-empty">no active task</div>';
    return;
  }

  const pct = todo.total_count ? Math.round((todo.completed_count / todo.total_count) * 100) : 0;
  $todoContent.innerHTML = `
    <div class="todo-block">
      <div class="todo-header">
        <span>TODO ${todo.completed_count}/${todo.total_count}</span>
        <div class="todo-progress-bar">
          <div class="todo-progress-fill" style="width:${pct}%"></div>
        </div>
      </div>
      ${todo.tasks.map(t => `
        <div class="todo-item ${t.completed ? 'completed' : ''}">
          <div class="todo-check"><div class="todo-check-inner"></div></div>
          <span>${escapeHtml(t.description)}</span>
        </div>
      `).join('')}
    </div>
  `;
  console.log('Todo display updated');
}

function startTodoPolling() {
  if (todoPollInterval) clearInterval(todoPollInterval);
  loadTodo();
  todoPollInterval = setInterval(loadTodo, POLL_INTERVAL);
}

// ── skills & tools ──

async function loadSkills() {
  try {
    const res = await fetch(`${API}/api/skills`);
    const data = await res.json();

    if (!data.skills || data.skills.length === 0) {
      $skillsList.innerHTML = '<div class="list-loading">no skills</div>';
      return;
    }

    $skillsList.innerHTML = data.skills.map(s => `
      <div class="skill-item">
        <div class="skill-item-name">${escapeHtml(s.id)}</div>
        <div class="skill-item-desc">${escapeHtml(s.description)}</div>
      </div>
    `).join('');
  } catch (e) {
    $skillsList.innerHTML = '<div class="list-loading">failed to load</div>';
  }
}

async function loadTools() {
  try {
    const res = await fetch(`${API}/api/tools`);
    const data = await res.json();

    if (!data.tools || data.tools.length === 0) {
      $toolsList.innerHTML = '<div class="list-loading">no tools</div>';
      return;
    }

    $toolsList.innerHTML = data.tools.map(t => `
      <div class="tool-item">
        <div class="tool-item-name">${escapeHtml(t.name)}</div>
        <div class="tool-item-desc">${escapeHtml(t.description)}</div>
      </div>
    `).join('');
  } catch (e) {
    $toolsList.innerHTML = '<div class="list-loading">failed to load</div>';
  }
}

// ── tabs ──

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
  });
});

// ── parse SSE ──

function parseSSE(line) {
  if (line.startsWith('data: ')) {
    const data = line.slice(6);
    try {
      return JSON.parse(data);
    } catch (e) {
      console.error('Failed to parse SSE data:', data);
      return null;
    }
  }
  return null;
}

// ── streaming chat ──

async function sendMessage(text) {
  setBusy(true);
  setLoading(true, '连接中...');
  appendUserMessage(text);

  // 取消之前的请求
  if (currentAbortController) {
    currentAbortController.abort();
  }
  currentAbortController = new AbortController();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, thread_id: threadId }),
      signal: currentAbortController.signal,
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;

        const event = parseSSE(line);
        if (!event) continue;

        switch (event.type) {
          case 'thread_id':
            updateThread(event.thread_id);
            break;

          case 'status':
            setLoading(true, event.message);
            break;

          case 'todo_created':
            // 直接使用事件中的 items 显示 TODO
            console.log('todo_created event:', event);
            if (event.items && event.items.length > 0) {
              // 后端发送的 items 已经是 {description, completed} 格式
              updateTodoDisplay({
                tasks: event.items,
                completed_count: 0,
                total_count: event.items.length,
              });
            } else {
              console.warn('todo_created event has no items:', event);
            }
            break;

          case 'tool_calls':
            appendToolCalls(event.tools);
            break;

          case 'response':
            appendAssistantMessage(renderMarkdown(event.content));
            break;

          case 'auto_continue':
            appendIterationBlock('AUTO CONTINUE', event.content);
            break;

          case 'note':
            appendIterationBlock('NOTE', event.content);
            break;

          case 'todo':
            updateTodoDisplay(event.todo);
            break;

          case 'todo_deleted':
            $todoContent.innerHTML = '<div class="todo-empty">task completed</div>';
            break;

          case 'error':
            appendError(event.message);
            break;

          case 'done':
            setLoading(false);
            break;
        }
      }
    }

  } catch (e) {
    if (e.name === 'AbortError') {
      // 请求被取消，忽略
    } else {
      setLoading(false);
      appendError(e.message);
    }
  }

  setBusy(false);
  currentAbortController = null;
  scrollToBottom();
}

async function newChat() {
  try {
    const res = await fetch(`${API}/api/new`, { method: 'POST' });
    const data = await res.json();
    updateThread(data.thread_id);
    $messages.innerHTML = '';
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.id = 'empty-state';
    empty.innerHTML = `
      <div class="empty-state-title">onekiil4all</div>
      <div class="empty-state-sub">send a message to begin</div>
    `;
    $messages.appendChild(empty);
    loadHistory();
  } catch (e) {
    console.error(e);
  }
}

// ── events ──

$send.addEventListener('click', async () => {
  const text = $input.value.trim();
  if (!text) return;

  $input.value = '';
  $input.style.height = 'auto';

  if (busy) {
    addPendingMessage(text);
  } else {
    await sendMessage(text);
  }
});

$input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    $send.click();
  }
});

$input.addEventListener('input', () => {
  $input.style.height = 'auto';
  $input.style.height = Math.min($input.scrollHeight, 100) + 'px';
});

$btnNew.addEventListener('click', () => {
  clearPendingQueue();
  if (!busy) newChat();
});

$btnClearPending.addEventListener('click', clearPendingQueue);
$btnRefreshHistory.addEventListener('click', loadHistory);
$btnRefreshTodo.addEventListener('click', loadTodo);

// ── init ──
newChat();
loadSkills();
loadTools();
