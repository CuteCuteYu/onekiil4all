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
const $btnRefreshTrends = document.getElementById('btn-refresh-trends');
const $hotsearchList = document.getElementById('hotsearch-list');
const $githubList = document.getElementById('github-list');
const $techList = document.getElementById('tech-list');

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

function appendProgressMessage(text, type = 'info') {
  removeEmptyState();
  const el = document.createElement('div');
  el.className = 'msg';
  
  let role = 'INFO';
  let style = 'color: var(--fg-dim); font-style: italic;';
  
  if (type === 'success') {
    role = 'SUCCESS';
    style = 'color: var(--success);';
  } else if (type === 'warning') {
    role = 'WARNING';
    style = 'color: var(--warning);';
  } else if (type === 'error') {
    role = 'ERROR';
    style = 'color: var(--error);';
  }
  
  el.innerHTML = `
    <div class="msg-role">${role}</div>
    <div class="msg-body" style="${style}">${escapeHtml(text)}</div>
  `;
  $messages.appendChild(el);
  scrollToBottom();
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
  
  // 创建工具调用容器
  const container = document.createElement('div');
  container.className = 'tool-calls-container';
  
  // 添加标题
  const titleEl = document.createElement('div');
  titleEl.className = 'msg';
  titleEl.innerHTML = `
    <div class="msg-role">TOOLS</div>
    <div class="tool-call-header">正在调用以下工具 (${toolCalls.length}个):</div>
  `;
  container.appendChild(titleEl);
  $messages.appendChild(container);
  scrollToBottom();
  
  // 逐个添加工具调用（带延迟动画效果）
  toolCalls.forEach((tool, index) => {
    setTimeout(() => {
      const toolEl = document.createElement('div');
      toolEl.className = 'msg tool-call-item';
      
      // 为不同的工具类型添加不同的描述
      let description = '';
      let status = '调用中...';
      
      if (tool.name.includes('search') || tool.name.includes('Search')) {
        description = '正在搜索信息...';
      } else if (tool.name.includes('read') || tool.name.includes('Read')) {
        description = '正在读取文件...';
      } else if (tool.name.includes('write') || tool.name.includes('Write')) {
        description = '正在写入文件...';
      } else if (tool.name.includes('bash') || tool.name.includes('Bash')) {
        description = '正在执行命令...';
      } else if (tool.name.includes('edit') || tool.name.includes('Edit')) {
        description = '正在编辑文件...';
      } else {
        description = '正在执行操作...';
      }
      
      toolEl.innerHTML = `
        <div class="msg-role">TOOL ${index + 1}</div>
        <div class="tool-call-content">
          <div class="tool-call-name">${escapeHtml(tool.name)}</div>
          <div class="tool-call-desc">${escapeHtml(description)}</div>
          <div class="tool-call-status">${escapeHtml(status)}</div>
        </div>
      `;
      
      container.appendChild(toolEl);
      scrollToBottom();
      
      // 模拟工具执行完成（实际应由后端发送完成事件）
      setTimeout(() => {
        const statusEl = toolEl.querySelector('.tool-call-status');
        if (statusEl) {
          statusEl.textContent = '✓ 完成';
          statusEl.style.color = 'var(--success)';
        }
      }, 800 + index * 400);
      
    }, index * 500); // 每个工具延迟500ms显示
  });
}

function appendSingleToolCall(toolName, description = '', status = '', index = 0, total = 1) {
  removeEmptyState();
  const el = document.createElement('div');
  el.className = 'msg tool-call-item';
  el.innerHTML = `
    <div class="msg-role">TOOL ${index + 1}/${total}</div>
    <div class="tool-call-content">
      <div class="tool-call-name">${escapeHtml(toolName)}</div>
      ${description ? `<div class="tool-call-desc">${escapeHtml(description)}</div>` : ''}
      ${status ? `<div class="tool-call-status">${escapeHtml(status)}</div>` : ''}
    </div>
  `;
  $messages.appendChild(el);
  scrollToBottom();
  return el;
}

function handleToolCallEvent(event) {
  const toolName = event.name || '未知工具';
  const status = event.status || '';
  const index = event.index || 0;
  const total = event.total || 1;
  
  // 根据工具名称生成描述
  let description = '';
  if (toolName.includes('search') || toolName.includes('Search')) {
    description = '搜索网络信息';
  } else if (toolName.includes('read') || toolName.includes('Read')) {
    description = '读取文件内容';
  } else if (toolName.includes('write') || toolName.includes('Write')) {
    description = '写入文件';
  } else if (toolName.includes('bash') || toolName.includes('Bash')) {
    description = '执行系统命令';
  } else if (toolName.includes('edit') || toolName.includes('Edit')) {
    description = '编辑文件';
  } else if (toolName.includes('glob') || toolName.includes('Glob')) {
    description = '查找文件';
  } else if (toolName.includes('grep') || toolName.includes('Grep')) {
    description = '搜索文件内容';
  } else {
    description = '执行操作';
  }
  
  // 查找是否已有该工具的元素
  const existingTool = document.querySelector(`[data-tool-name="${toolName}"][data-tool-index="${index}"]`);
  
  if (existingTool) {
    // 更新现有工具状态
    const statusEl = existingTool.querySelector('.tool-call-status');
    if (statusEl) {
      statusEl.textContent = status;
      
      // 根据状态设置颜色
      if (status.includes('✓') || status.includes('完成')) {
        statusEl.style.color = 'var(--success)';
      } else if (status.includes('执行中') || status.includes('...')) {
        statusEl.style.color = 'var(--warning)';
      } else if (status.includes('失败') || status.includes('错误')) {
        statusEl.style.color = 'var(--error)';
      }
    }
  } else {
    // 创建新的工具调用显示
    const el = appendSingleToolCall(toolName, description, status, index, total);
    el.setAttribute('data-tool-name', toolName);
    el.setAttribute('data-tool-index', index);
    
    // 根据状态设置初始颜色
    const statusEl = el.querySelector('.tool-call-status');
    if (statusEl) {
      if (status.includes('✓') || status.includes('完成')) {
        statusEl.style.color = 'var(--success)';
      } else if (status.includes('执行中') || status.includes('...')) {
        statusEl.style.color = 'var(--warning)';
      }
    }
  }
  
  // 如果是第一个工具，显示进度消息
  if (index === 0 && status.includes('开始调用')) {
    appendProgressMessage(`开始执行 ${total} 个工具调用`, 'info');
  }
  
  // 如果是最后一个工具完成，显示完成消息
  if (index === total - 1 && (status.includes('✓') || status.includes('完成'))) {
    appendProgressMessage(`所有工具调用完成`, 'success');
  }
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
        <span class="history-item-delete" data-delete="${item.thread_id}">DEL</span>
        <div class="history-item-thread">${item.thread_id.slice(0, 12)}...</div>
        <div class="history-item-preview">${escapeHtml(item.last_message || 'empty')}</div>
      </div>
    `).join('');

    $historyList.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target.classList.contains('history-item-delete')) return;
        loadChatHistory(el.dataset.thread);
      });
    });

    $historyList.querySelectorAll('.history-item-delete').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteHistory(el.dataset.delete);
      });
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

// ── intelligence / trends ──

async function loadTrends() {
  try {
    const res = await fetch(`${API}/api/trends`);
    const data = await res.json();

    if (data.hot_search && data.hot_search.length > 0 && data.hot_search[0].word !== "暂无数据") {
      const grouped = {};
      data.hot_search.forEach(item => {
        const source = item.source || 'other';
        if (!grouped[source]) grouped[source] = [];
        grouped[source].push(item);
      });
      
      let html = '';
      for (const [source, items] of Object.entries(grouped)) {
        html += `<div class="trend-group"><div class="trend-group-header">${escapeHtml(source)}</div>`;
        html += items.map((item, i) => {
          const linkUrl = item.url || '#';
          return `
          <div class="trend-item">
            <div class="trend-item-meta">
              <span class="trend-item-rank">${i + 1}</span>
            </div>
            <div class="trend-item-title">
              <a href="${escapeHtml(linkUrl)}" target="_blank" rel="noopener">${escapeHtml(item.word || item.raw_word)}</a>
            </div>
          </div>`;
        }).join('');
        html += '</div>';
      }
      $hotsearchList.innerHTML = html;
    } else {
      $hotsearchList.innerHTML = '<div class="list-loading">no data</div>';
    }

    if (data.github && data.github.length > 0 && data.github[0].name !== "暂无数据") {
      $githubList.innerHTML = data.github.map(item => `
        <div class="trend-item">
          <div class="trend-item-github">
            <div class="trend-item-github-name">
              <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener">${escapeHtml(item.name)}</a>
            </div>
            ${item.description ? `<div class="trend-item-github-desc">${escapeHtml(item.description)}</div>` : ''}
            <div class="trend-item-github-stats">
              <span class="trend-item-github-lang">${escapeHtml(item.language || '')}</span>
            </div>
          </div>
        </div>
      `).join('');
    } else {
      $githubList.innerHTML = '<div class="list-loading">no data</div>';
    }

    if (data.tech_news && data.tech_news.length > 0 && data.tech_news[0].title !== "暂无数据") {
      $techList.innerHTML = data.tech_news.map(item => `
        <div class="trend-item">
          <div class="trend-item-meta">
            <span class="trend-source-tag">${escapeHtml(item.source || '')}</span>
          </div>
          <div class="trend-item-title">
            <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>
          </div>
        </div>
      `).join('');
    } else {
      $techList.innerHTML = '<div class="list-loading">no data</div>';
    }

  } catch (e) {
    $hotsearchList.innerHTML = '<div class="list-error">加载失败</div>';
    $githubList.innerHTML = '<div class="list-error">加载失败</div>';
    $techList.innerHTML = '<div class="list-error">加载失败</div>';
  }
}

// ── tabs ──

document.querySelectorAll('.intelligence-tabs .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.intelligence-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.intelligence-content .tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.dataset.tab;
    const panel = document.getElementById(`tab-${tabId}`);
    if (panel) {
      panel.classList.add('active');
    }
  });
});

document.querySelectorAll('.tools-tabs .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tools-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tools-content .tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.dataset.tab;
    const panel = document.getElementById(`tab-${tabId}`);
    if (panel) {
      panel.classList.add('active');
    }
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
    appendProgressMessage('正在连接到服务器...', 'info');
    
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, thread_id: threadId }),
      signal: currentAbortController.signal,
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    
    appendProgressMessage('连接成功，开始处理请求...', 'success');

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
             appendProgressMessage(`对话线程已创建: ${event.thread_id.slice(0, 8)}...`, 'info');
             break;

           case 'status':
             setLoading(true, event.message);
             appendProgressMessage(`状态: ${event.message}`, 'info');
             break;

           case 'todo_created':
             // 直接使用事件中的 items 显示 TODO
             console.log('todo_created event:', event);
             if (event.items && event.items.length > 0) {
               appendProgressMessage(`已创建任务列表，共 ${event.items.length} 个任务`, 'success');
               // 后端发送的 items 已经是 {description, completed} 格式
               updateTodoDisplay({
                 tasks: event.items,
                 completed_count: 0,
                 total_count: event.items.length,
               });
             } else {
               console.warn('todo_created event has no items:', event);
               appendProgressMessage('任务列表创建失败，未获取到任务项', 'warning');
             }
             break;

           case 'tool_calls':
             if (event.tools && event.tools.length > 0) {
               const toolNames = event.tools.map(t => t.name || '未知工具').join(', ');
               appendProgressMessage(`正在调用工具: ${toolNames}`, 'info');
             }
             appendToolCalls(event.tools);
             break;
             
           case 'tool_call':
             // 单个工具调用事件
             handleToolCallEvent(event);
             break;

           case 'response':
             appendProgressMessage('正在生成最终响应...', 'info');
             appendAssistantMessage(renderMarkdown(event.content));
             appendProgressMessage('响应生成完成', 'success');
             break;

           case 'auto_continue':
             appendProgressMessage('检测到任务未完成，自动继续执行...', 'info');
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
             appendProgressMessage(`错误: ${event.message}`, 'error');
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
   appendProgressMessage('本次对话处理完成', 'success');
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
$btnRefreshTrends.addEventListener('click', loadTrends);

// ── init ──
newChat();
loadSkills();
loadTools();
loadTrends();

// 监听窗口大小变化
window.addEventListener('resize', () => {
  // 可以在这里添加resize处理逻辑
});

// 定期检查输入框状态（只检查不修改布局）
setInterval(() => {
  // 只确保输入框可聚焦，不修改其他样式
  if (!$input.hasAttribute('tabindex')) {
    $input.setAttribute('tabindex', '0');
  }
}, 2000);

// ── resizable sidebars ──

function initResizers() {
  const app = document.getElementById('app');
  
  // 创建左侧拖动条 (intelligence)
  const resizerLeft = document.createElement('div');
  resizerLeft.className = 'resizer resizer-left';
  resizerLeft.id = 'resizer-left';
  app.appendChild(resizerLeft);
  
  // 创建左侧第二个拖动条 (history)
  const resizerLeft2 = document.createElement('div');
  resizerLeft2.className = 'resizer resizer-left-2';
  resizerLeft2.id = 'resizer-left-2';
  app.appendChild(resizerLeft2);
  
  // 创建右侧拖动条
  const resizerRight = document.createElement('div');
  resizerRight.className = 'resizer resizer-right';
  resizerRight.id = 'resizer-right';
  app.appendChild(resizerRight);
  
  let currentResizer = null;
  let startX = 0;
  let startSidebarWidth = 0;
  
  // 拖动开始
  function initDrag(e, resizer) {
    currentResizer = resizer;
    startX = e.pageX;
    
    if (resizer.id === 'resizer-left') {
      startSidebarWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--intelligence-width')) || 280;
    } else if (resizer.id === 'resizer-left-2') {
      startSidebarWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width')) || 220;
    } else {
      startSidebarWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--right-sidebar-width')) || 220;
    }
    
    resizer.classList.add('active');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }
  
  // 拖动中
  function doDrag(e) {
    if (!currentResizer) return;
    
    const diffX = e.pageX - startX;
    let newWidth;
    
    if (currentResizer.id === 'resizer-left') {
      // intelligence 侧边栏
      newWidth = startSidebarWidth + diffX;
      newWidth = Math.max(200, Math.min(400, newWidth));
      document.documentElement.style.setProperty('--intelligence-width', newWidth + 'px');
    } else if (currentResizer.id === 'resizer-left-2') {
      // history 侧边栏
      newWidth = startSidebarWidth + diffX;
      newWidth = Math.max(150, Math.min(350, newWidth));
      document.documentElement.style.setProperty('--sidebar-width', newWidth + 'px');
    } else if (currentResizer.id === 'resizer-right') {
      // 右侧侧边栏
      newWidth = startSidebarWidth - diffX;
      newWidth = Math.max(180, Math.min(350, newWidth));
      document.documentElement.style.setProperty('--right-sidebar-width', newWidth + 'px');
    }
    
    // 更新拖动条位置
    updateResizerPositions();
  }
  
  // 拖动结束
  function endDrag() {
    if (currentResizer) {
      currentResizer.classList.remove('active');
      currentResizer = null;
    }
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
  
  // 更新拖动条位置
  function updateResizerPositions() {
    const intelligenceWidth = getComputedStyle(document.documentElement).getPropertyValue('--intelligence-width').trim();
    const sidebarWidth = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width').trim();
    const rightSidebarWidth = getComputedStyle(document.documentElement).getPropertyValue('--right-sidebar-width').trim();
    
    resizerLeft.style.left = intelligenceWidth + 'px';
    resizerLeft2.style.left = (parseInt(intelligenceWidth) + parseInt(sidebarWidth)) + 'px';
    resizerRight.style.right = rightSidebarWidth + 'px';
  }
  
  // 绑定事件
  resizerLeft.addEventListener('mousedown', (e) => initDrag(e, resizerLeft));
  resizerLeft2.addEventListener('mousedown', (e) => initDrag(e, resizerLeft2));
  resizerRight.addEventListener('mousedown', (e) => initDrag(e, resizerRight));
  
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', endDrag);
  
  // 初始化位置
  updateResizerPositions();
  
  // 窗口大小变化时更新位置
  window.addEventListener('resize', updateResizerPositions);
}


