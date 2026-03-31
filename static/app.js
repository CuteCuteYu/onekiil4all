/**
 * 上古必斩必杀 应用程序主脚本
 * 负责处理前端聊天界面与后端API的所有交互
 * 包含功能：消息发送/接收、历史记录管理、待办事项、工具调用、热点资讯等
 */

// ═══════════════════════════════════════════════════════════════
// 配置部分
// ═══════════════════════════════════════════════════════════════

/**
 * API基础URL
 * 为空字符串表示使用相对路径，当前域名的API端点
 */
const API = '';

/**
 * 轮询间隔时间 (毫秒)
 * 用于定期刷新待办事项和热点资讯
 */
const POLL_INTERVAL = 2000;


// ═══════════════════════════════════════════════════════════════
// 状态管理
// ═══════════════════════════════════════════════════════════════

/**
 * 当前对话线程的唯一标识符
 * 用于区分不同的聊天会话
 */
let threadId = null;

/**
 * 忙碌状态标志
 * 当AI正在处理请求时为true，此时用户输入会被放入待发送队列
 */
let busy = false;

/**
 * 待发送消息队列
 * 当AI忙碌时，用户输入的消息会暂存到这里
 */
let pendingMessages = [];

/**
 * 待办事项轮询定时器
 * 用于定期获取待办事项更新
 */
let todoPollInterval = null;

/**
 * 当前请求的AbortController
 * 用于取消正在进行的API请求
 */
let currentAbortController = null;


// ═══════════════════════════════════════════════════════════════
// DOM元素缓存
// ═══════════════════════════════════════════════════════════════

/**
 * 获取页面中所有需要操作的DOM元素
 * 缓存这些元素以提高性能，避免重复查询
 */
const $messages = document.getElementById('messages');           // 消息列表容器
const $input = document.getElementById('msg-input');              // 消息输入框
const $send = document.getElementById('btn-send');                 // 发送按钮
const $loading = document.getElementById('loading');               // 加载指示器
const $loadingText = document.getElementById('loading-text');     // 加载状态文本
const $threadBadge = document.getElementById('thread-badge');     // 线程ID徽章
const $btnNew = document.getElementById('btn-new');               // 新建对话按钮
const $historyList = document.getElementById('history-list');      // 历史记录列表
const $todoContent = document.getElementById('todo-content');     // 待办事项内容
const $skillsList = document.getElementById('skills-list');        // 技能列表
const $toolsList = document.getElementById('tools-list');         // 工具列表
const $pendingQueue = document.getElementById('pending-queue');   // 待发送队列
const $pendingList = document.getElementById('pending-list');     // 待发送消息列表
const $btnClearPending = document.getElementById('btn-clear-pending'); // 清空待发送按钮
const $btnRefreshHistory = document.getElementById('btn-refresh-history'); // 刷新历史按钮
const $btnRefreshTodo = document.getElementById('btn-refresh-todo'); // 刷新待办按钮
const $btnRefreshTrends = document.getElementById('btn-refresh-trends'); // 刷新热点按钮
const $hotsearchList = document.getElementById('hotsearch-list'); // 热搜列表
const $githubList = document.getElementById('github-list');       // GitHub趋势列表
const $techList = document.getElementById('tech-list');           // 科技新闻列表
const $alertsList = document.getElementById('alerts-list');       // 告警列表
const $alertHistoryList = document.getElementById('alert-history-list'); // 告警历史列表
const $alertInput = document.getElementById('alert-input');       // 告警输入框
const $btnAddAlert = document.getElementById('btn-add-alert');    // 添加告警按钮
const $btnRefreshAlerts = document.getElementById('btn-refresh-alerts'); // 刷新告警按钮
const $btnClearAlertHistory = document.getElementById('btn-clear-alert-history'); // 清空告警历史按钮


// ═══════════════════════════════════════════════════════════════
// marked.js 配置
// ═══════════════════════════════════════════════════════════════

/**
 * 配置Markdown解析器 marked
 * 设置代码高亮和Markdown渲染选项
 */
marked.setOptions({
  /**
   * 代码高亮函数
   * @param {string} code - 代码内容
   * @param {string} lang - 编程语言标识
   * @returns {string} 高亮后的HTML
   */
  highlight: (code, lang) => {
    // 如果指定了语言且该语言支持，则使用对应语言高亮
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    // 否则自动检测语言
    return hljs.highlightAuto(code).value;
  },
  // 允许换行符转换为<br>标签
  breaks: true,
  // 启用GitHub风格的Markdown
  gfm: true,
});


// ═══════════════════════════════════════════════════════════════
// 辅助函数
// ═══════════════════════════════════════════════════════════════

/**
 * 将消息列表滚动到底部
 * 确保最新消息始终可见
 */
function scrollToBottom() {
  $messages.scrollTop = $messages.scrollHeight;
}

/**
 * 设置加载状态
 * @param {boolean} on - 是否显示加载状态
 * @param {string} text - 可选的加载状态文本
 */
function setLoading(on, text) {
  $loading.classList.toggle('active', on);
  if (text) $loadingText.textContent = text;
}

/**
 * 添加进度消息
 * 用于显示系统状态、警告、错误等信息
 * @param {string} text - 消息内容
 * @param {string} type - 消息类型: 'info', 'success', 'warning', 'error'
 */
function appendProgressMessage(text, type = 'info') {
  removeEmptyState();
  const el = document.createElement('div');
  el.className = 'msg';
  
  // 根据消息类型设置不同的样式
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

/**
 * 设置忙碌状态
 * 忙碌时禁用发送按钮，并将新消息加入待发送队列
 * @param {boolean} on - 是否忙碌
 */
function setBusy(on) {
  busy = on;
  $send.disabled = on;
}

/**
 * 更新当前对话线程
 * @param {string} id - 新的线程ID
 */
function updateThread(id) {
  threadId = id;
  // 显示线程ID的前8位
  $threadBadge.textContent = id ? id.slice(0, 8) : '';
  // 启动待办事项轮询
  startTodoPolling();
  // 加载历史记录
  loadHistory();
}

/**
 * 移除空状态提示
 * 当有消息时隐藏初始的空状态界面
 */
function removeEmptyState() {
  const el = document.getElementById('empty-state');
  if (el) el.remove();
}

/**
 * HTML转义函数
 * 防止XSS攻击，将特殊字符转换为HTML实体
 * @param {string} s - 原始字符串
 * @returns {string} 转义后的字符串
 */
function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

/**
 * Markdown渲染函数
 * 将Markdown文本转换为HTML
 * @param {string} text - Markdown文本
 * @returns {string} 渲染后的HTML
 */
function renderMarkdown(text) {
  return marked.parse(text);
}


// ═══════════════════════════════════════════════════════════════
// 消息渲染函数
// ═══════════════════════════════════════════════════════════════

/**
 * 添加用户消息到界面
 * @param {string} text - 用户输入的文本
 */
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

/**
 * 添加助手回复到界面
 * @param {string} html - 渲染后的HTML内容
 */
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

/**
 * 显示工具调用信息
 * 展示AI正在调用的工具列表
 * @param {Array} toolCalls - 工具调用数组
 */
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

/**
 * 添加单个工具调用显示
 * 用于实时更新工具执行状态
 * @param {string} toolName - 工具名称
 * @param {string} description - 工具描述
 * @param {string} status - 执行状态
 * @param {number} index - 工具索引
 * @param {number} total - 工具总数
 * @returns {HTMLElement} 创建的元素
 */
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

/**
 * 处理工具调用事件
 * 根据后端推送的工具调用事件更新界面
 * @param {Object} event - 工具调用事件对象
 */
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

/**
 * 添加迭代/继续块
 * 用于显示任务自动继续执行的内容
 * @param {string} label - 块标签 (如 'AUTO CONTINUE', 'NOTE')
 * @param {string} content - 块内容
 */
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

/**
 * 添加摘要块
 * 用于显示最终响应摘要
 * @param {string} content - 摘要内容 (Markdown格式)
 */
function appendSummary(content) {
  const el = document.createElement('div');
  el.className = 'msg';
  el.innerHTML = `<div class="summary-block">${renderMarkdown(content)}</div>`;
  $messages.appendChild(el);
  scrollToBottom();
}

/**
 * 添加错误消息
 * @param {string} msg - 错误信息
 */
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


// ═══════════════════════════════════════════════════════════════
// 待发送消息队列管理
// ═══════════════════════════════════════════════════════════════

/**
 * 更新待发送队列显示
 * 根据pendingMessages数组重新渲染队列界面
 */
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

/**
 * 添加消息到待发送队列
 * 当AI忙碌时调用
 * @param {string} text - 待发送的消息文本
 */
function addPendingMessage(text) {
  pendingMessages.push(text);
  updatePendingQueue();
}

/**
 * 清空待发送队列
 * 用户点击清空按钮时调用
 */
function clearPendingQueue() {
  pendingMessages = [];
  updatePendingQueue();
}

/**
 * 发送待发送队列中的所有消息
 * 按顺序逐条发送队列中的消息
 */
async function sendPendingMessages() {
  const messages = [...pendingMessages];
  pendingMessages = [];
  updatePendingQueue();

  for (const msg of messages) {
    await sendMessage(msg);
  }
}


// ═══════════════════════════════════════════════════════════════
// 历史记录管理
// ═══════════════════════════════════════════════════════════════

/**
 * 加载对话历史记录列表
 * 从API获取所有历史对话记录并显示在侧边栏
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
      <div class="history-item ${item.thread_id === threadId ? 'active' : ''}" data-thread="${item.thread_id}">
        <span class="history-item-delete" data-delete="${item.thread_id}">DEL</span>
        <div class="history-item-thread">${item.thread_id.slice(0, 12)}...</div>
        <div class="history-item-preview">${escapeHtml(item.last_message || 'empty')}</div>
      </div>
    `).join('');

    // 绑定点击事件 - 加载历史对话
    $historyList.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target.classList.contains('history-item-delete')) return;
        loadChatHistory(el.dataset.thread);
      });
    });

    // 绑定删除事件
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

/**
 * 加载指定历史对话
 * @param {string} tid - 线程ID
 */
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
         <div class="empty-state-title">上古必斩必杀</div>
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

/**
 * 删除历史记录
 * @param {string} tid - 要删除的线程ID
 */
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


// ═══════════════════════════════════════════════════════════════
// 待办事项管理
// ═══════════════════════════════════════════════════════════════

/**
 * 加载待办事项
 * 根据当前线程ID从API获取待办任务列表
 */
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

/**
 * 更新待办事项显示
 * 用于实时更新待办任务状态
 * @param {Object} todo - 待办事项对象
 */
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

/**
 * 启动待办事项轮询
 * 定期刷新待办事项状态
 */
function startTodoPolling() {
  if (todoPollInterval) clearInterval(todoPollInterval);
  loadTodo();
  todoPollInterval = setInterval(loadTodo, POLL_INTERVAL);
}


// ═══════════════════════════════════════════════════════════════
// 技能和工具管理
// ═══════════════════════════════════════════════════════════════

/**
 * 加载可用技能列表
 * 从API获取所有可用的AI技能
 */
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

/**
 * 加载可用工具列表
 * 从API获取所有可用的AI工具
 */
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


// ═══════════════════════════════════════════════════════════════
// 热点资讯管理
// ═══════════════════════════════════════════════════════════════

/**
 * 加载热点资讯
 * 从API获取热搜、GitHub趋势、科技新闻等数据
 */
async function loadTrends() {
  try {
    const res = await fetch(`${API}/api/trends`);
    const data = await res.json();

    // 处理热搜数据
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

    // 处理GitHub趋势数据
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

    // 处理科技新闻数据
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


// ═══════════════════════════════════════════════════════════════
// 告警管理
// ═══════════════════════════════════════════════════════════════

/**
 * 加载告警列表
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

/**
 * 添加告警
 */
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

/**
 * 切换告警状态
 */
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

/**
 * 删除告警
 */
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

/**
 * 启动告警流监听
 * 接收后端推送的新告警事件
 */
function startAlertStream() {
  const eventSource = new EventSource(`${API}/api/alerts/stream`);
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'alert' && data.event) {
        const alertEvent = data.event;
        handleNewAlert(alertEvent);
      } else if (data.type === 'ping') {
        // 心跳，保持连接
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

/**
 * 处理新告警事件
 */
function handleNewAlert(alertEvent) {
  appendProgressMessage(`[告警] ${alertEvent.keyword}: ${alertEvent.title}`, 'warning');
  loadAlertHistory();
  
  if ($alertsList.querySelector('.alert-empty')) {
    loadAlerts();
  }
}

/**
 * 加载告警历史
 */
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

/**
 * 格式化告警时间
 */
function formatAlertTime(isoString) {
  if (!isoString) return '--';
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

/**
 * 清空告警历史
 */
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


// ═══════════════════════════════════════════════════════════════
// 标签页切换功能
// ═══════════════════════════════════════════════════════════════

/**
 * 初始化右侧热点资讯面板的标签页切换
 * 支持：热搜 / GitHub / 科技新闻 三个标签
 */
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

/**
 * 初始化左侧技能/工具面板的标签页切换
 * 支持：技能 / 工具 两个标签
 */
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


// ═══════════════════════════════════════════════════════════════
// SSE事件解析
// ═══════════════════════════════════════════════════════════════

/**
 * 解析Server-Sent Events (SSE) 事件行
 * 从SSE格式的文本中提取JSON数据
 * @param {string} line - SSE事件行
 * @returns {Object|null} 解析后的数据对象
 */
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


// ═══════════════════════════════════════════════════════════════
// 流式聊天功能
// ═══════════════════════════════════════════════════════════════

/**
 * 发送消息并处理响应
 * 使用流式API接收AI响应，实时更新界面
 * @param {string} text - 用户消息内容
 */
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
    
    // 发送POST请求到聊天API
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

    // 获取响应流
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    // 持续读取流数据
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      // 处理每一行SSE事件
      for (const line of lines) {
        if (!line.trim()) continue;

        const event = parseSSE(line);
        if (!event) continue;

        // 根据事件类型处理不同的消息
        switch (event.type) {
          // 新线程创建事件
          case 'thread_id':
            updateThread(event.thread_id);
            appendProgressMessage(`对话线程已创建: ${event.thread_id.slice(0, 8)}...`, 'info');
            break;

          // 状态更新事件
          case 'status':
            setLoading(true, event.message);
            appendProgressMessage(`状态: ${event.message}`, 'info');
            break;

          // 待办事项创建事件
          case 'todo_created':
            console.log('todo_created event:', event);
            if (event.items && event.items.length > 0) {
              appendProgressMessage(`已创建任务列表，共 ${event.items.length} 个任务`, 'success');
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

          // 工具调用列表事件
          case 'tool_calls':
            if (event.tools && event.tools.length > 0) {
              const toolNames = event.tools.map(t => t.name || '未知工具').join(', ');
              appendProgressMessage(`正在调用工具: ${toolNames}`, 'info');
            }
            appendToolCalls(event.tools);
            break;
            
          // 单个工具调用事件
          case 'tool_call':
            handleToolCallEvent(event);
            break;

          // AI最终响应事件
          case 'response':
            appendProgressMessage('正在生成最终响应...', 'info');
            appendAssistantMessage(renderMarkdown(event.content));
            appendProgressMessage('响应生成完成', 'success');
            break;

          // 自动继续执行事件
          case 'auto_continue':
            appendProgressMessage('检测到任务未完成，自动继续执行...', 'info');
            appendIterationBlock('AUTO CONTINUE', event.content);
            break;

          // 笔记/备注事件
          case 'note':
            appendIterationBlock('NOTE', event.content);
            break;

          // 待办事项更新事件
          case 'todo':
            updateTodoDisplay(event.todo);
            break;

          // 待办事项完成删除事件
          case 'todo_deleted':
            $todoContent.innerHTML = '<div class="todo-empty">task completed</div>';
            break;

          // 错误事件
          case 'error':
            appendProgressMessage(`错误: ${event.message}`, 'error');
            appendError(event.message);
            break;

          // 完成事件
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

/**
 * 创建新对话
 * 清空当前消息，创建新的线程
 */
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


// ═══════════════════════════════════════════════════════════════
// 事件绑定
// ═══════════════════════════════════════════════════════════════

// 发送按钮点击事件
$send.addEventListener('click', async () => {
  const text = $input.value.trim();
  if (!text) return;

  $input.value = '';
  $input.style.height = 'auto';

  if (busy) {
    // 如果AI忙碌，将消息加入待发送队列
    addPendingMessage(text);
  } else {
    // 否则立即发送
    await sendMessage(text);
  }
});

// 输入框键盘事件 - Enter发送，Shift+Enter换行
$input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    $send.click();
  }
});

// 输入框内容变化事件 - 自动调整输入框高度
$input.addEventListener('input', () => {
  $input.style.height = 'auto';
  $input.style.height = Math.min($input.scrollHeight, 100) + 'px';
});

// 新建对话按钮点击事件
$btnNew.addEventListener('click', () => {
  clearPendingQueue();
  if (!busy) newChat();
});

// 清空待发送队列按钮
$btnClearPending.addEventListener('click', clearPendingQueue);

// 刷新按钮事件绑定
$btnRefreshHistory.addEventListener('click', loadHistory);
$btnRefreshTodo.addEventListener('click', loadTodo);
$btnRefreshTrends.addEventListener('click', () => {
  loadTrends();
  loadAlerts();
  loadAlertHistory();
});
$btnAddAlert.addEventListener('click', () => {
  const keyword = $alertInput.value.trim();
  if (keyword) addAlert(keyword);
});
$alertInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const keyword = $alertInput.value.trim();
    if (keyword) addAlert(keyword);
  }
});
$btnClearAlertHistory.addEventListener('click', clearAlertHistory);

// LINKS 关联搜索
const $btnSearchLinks = document.getElementById('btn-search-links');
const $linkKeywordInput = document.getElementById('link-keyword-input');
const $linkResults = document.getElementById('link-results');

if ($btnSearchLinks) {
  $btnSearchLinks.addEventListener('click', searchLinks);
}
if ($linkKeywordInput) {
  $linkKeywordInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') searchLinks();
  });
}

async function searchLinks() {
  const keyword = $linkKeywordInput.value.trim();

  if (!keyword || keyword.length < 2) {
    $linkResults.innerHTML = '<div class="list-empty">请输入至少2个字符的关键词</div>';
    return;
  }

  $linkResults.innerHTML = '<div class="list-loading">loading...</div>';

  try {
    const res = await fetch(
      `${API}/api/trends/associations?keyword=${encodeURIComponent(keyword)}`
    );
    const data = await res.json();

    if (data.error) {
      $linkResults.innerHTML = `<div class="list-empty">${data.error}</div>`;
      return;
    }

    renderLinkResults(data);
  } catch (e) {
    console.error('Failed to search links:', e);
    $linkResults.innerHTML = '<div class="list-empty">load failed</div>';
  }
}

function renderLinkResults(data) {
  if (!data.associations || data.associations.length === 0) {
    $linkResults.innerHTML = '<div class="list-empty">no related keywords</div>';
    return;
  }

  $linkResults.innerHTML = data.associations.map(item => `
    <div class="link-result-item" data-keyword="${escapeHtml(item.keyword)}">
      <span class="kw-name">${escapeHtml(item.keyword)}</span>
      <span class="kw-score">${Math.round(item.score * 100)}%</span>
    </div>
  `).join('');

  $linkResults.querySelectorAll('.link-result-item').forEach(el => {
    el.addEventListener('click', async () => {
      const keyword = el.dataset.keyword;
      await addAlert(keyword);
      switchIntelligenceTab('alerts');
    });
  });
}

function switchIntelligenceTab(tabName) {
  document.querySelectorAll('.intelligence-tabs .tab-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabName);
  });
  document.querySelectorAll('.intelligence-content .tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabName}`);
  });
}


// ═══════════════════════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════════════════════

// 页面加载完成后初始化
newChat();       // 创建新对话
loadSkills();    // 加载技能列表
loadTools();     // 加载工具列表
loadTrends();    // 加载热点资讯
loadAlerts();    // 加载告警列表
loadAlertHistory(); // 加载告警历史
startAlertStream(); // 启动告警流监听

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


// ═══════════════════════════════════════════════════════════════
// 侧边栏拖拽调整大小功能
// ═══════════════════════════════════════════════════════════════

/**
 * 初始化侧边栏拖拽调整大小功能
 * 允许用户通过拖拽调整左右侧边栏的宽度
 */
function initResizers() {
  const app = document.getElementById('app');
  
  // 创建左侧拖动条 (intelligence侧边栏)
  const resizerLeft = document.createElement('div');
  resizerLeft.className = 'resizer resizer-left';
  resizerLeft.id = 'resizer-left';
  app.appendChild(resizerLeft);
  
  // 创建左侧第二个拖动条 (history侧边栏)
  const resizerLeft2 = document.createElement('div');
  resizerLeft2.className = 'resizer resizer-left-2';
  resizerLeft2.id = 'resizer-left-2';
  app.appendChild(resizerLeft2);
  
  // 创建右侧拖动条
  const resizerRight = document.createElement('div');
  resizerRight.className = 'resizer resizer-right';
  resizerRight.id = 'resizer-right';
  app.appendChild(resizerRight);
  
  // 拖拽状态变量
  let currentResizer = null;
  let startX = 0;
  let startSidebarWidth = 0;
  
  /**
   * 开始拖拽
   * @param {MouseEvent} e - 鼠标事件对象
   * @param {HTMLElement} resizer - 拖拽条元素
   */
  function initDrag(e, resizer) {
    currentResizer = resizer;
    startX = e.pageX;
    
    // 根据不同的拖拽条获取初始宽度
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
  
  /**
   * 拖拽过程中更新宽度
   * @param {MouseEvent} e - 鼠标事件对象
   */
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
  
  /**
   * 结束拖拽
   */
  function endDrag() {
    if (currentResizer) {
      currentResizer.classList.remove('active');
      currentResizer = null;
    }
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
  
  /**
   * 更新拖动条位置
   * 根据侧边栏宽度计算拖动条的left/right值
   */
  function updateResizerPositions() {
    const intelligenceWidth = getComputedStyle(document.documentElement).getPropertyValue('--intelligence-width').trim();
    const sidebarWidth = getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width').trim();
    const rightSidebarWidth = getComputedStyle(document.documentElement).getPropertyValue('--right-sidebar-width').trim();
    
    resizerLeft.style.left = intelligenceWidth + 'px';
    resizerLeft2.style.left = (parseInt(intelligenceWidth) + parseInt(sidebarWidth)) + 'px';
    resizerRight.style.right = rightSidebarWidth + 'px';
  }
  
  // 绑定拖拽事件监听器
  resizerLeft.addEventListener('mousedown', (e) => initDrag(e, resizerLeft));
  resizerLeft2.addEventListener('mousedown', (e) => initDrag(e, resizerLeft2));
  resizerRight.addEventListener('mousedown', (e) => initDrag(e, resizerRight));
  
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', endDrag);
  
  // 初始化拖动条位置
  updateResizerPositions();
  
  // 窗口大小变化时更新位置
  window.addEventListener('resize', updateResizerPositions);
}
