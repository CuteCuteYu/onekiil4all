/**
 * 上古必斩必杀 辅助函数
 */

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

function setBusyState(on) {
  busy = on;
  $send.disabled = on;
  $send.classList.toggle('busy', on);
}

function removeEmptyState() {
  const emptyState = document.getElementById('empty-state');
  if (emptyState) {
    emptyState.remove();
  }
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

/**
 * 渲染 Markdown 到指定元素（经 DOMPurify 消毒，
 * 阻止工具结果中夹带的 HTML/javascript: 链接被执行）
 */
function renderMarkdown(el, content) {
  el.innerHTML = DOMPurify.sanitize(marked.parse(content));
  el.querySelectorAll('pre code').forEach((block) => {
    // CDN 加载失败时跳过高亮，不中断渲染
    if (typeof hljs !== 'undefined') {
      hljs.highlightElement(block);
    }
  });
  scrollToBottom();
}

function renderMessage(role, content, metadata = null) {
  removeEmptyState();

  const isUser = role === 'user';
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="msg-role">${role.toUpperCase()}</div>
    <div class="msg-body"></div>
  `;

  const body = div.querySelector('.msg-body');
  if (isUser) {
    // 用户消息为纯文本转义
    body.innerHTML = escapeHtml(content);
  } else {
    // 助手消息为消毒后的 Markdown
    renderMarkdown(body, content);
  }

  if (metadata) {
    const metaDiv = document.createElement('div');
    metaDiv.className = 'msg-meta';

    if (metadata.iterations) {
      const iterDiv = document.createElement('span');
      iterDiv.className = 'msg-iterations';
      iterDiv.textContent = `${metadata.iterations.length} iterations`;
      metaDiv.appendChild(iterDiv);
    }

    if (metadata.tools) {
      const toolsDiv = document.createElement('span');
      toolsDiv.className = 'msg-tools';
      toolsDiv.textContent = `${metadata.tools.length} tools`;
      metaDiv.appendChild(toolsDiv);
    }

    if (metaDiv.children.length > 0) {
      div.appendChild(metaDiv);
    }
  }

  $messages.appendChild(div);
  scrollToBottom();
}

function renderLoadingMessage() {
  removeEmptyState();

  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = 'loading-msg';

  div.innerHTML = `
    <div class="msg-role">ASSISTANT</div>
    <div class="msg-body">
      <div class="loading-dots"><span></span><span></span><span></span></div>
    </div>
  `;

  $messages.appendChild(div);
  scrollToBottom();
}

function removeLoadingMessage() {
  const loadingMsg = document.getElementById('loading-msg');
  if (loadingMsg) {
    loadingMsg.remove();
  }
}

/**
 * 获取（不存在则创建）流式回复容器。
 * 用固定 id 定位而不是 ".msg.assistant:last-child"，
 * 避免 status 事件追加的 INFO 消息插在后面导致选择器失配。
 */
function ensureStreamingMessage() {
  removeEmptyState();
  removeLoadingMessage();

  let div = document.getElementById('streaming-msg');
  if (!div) {
    div = document.createElement('div');
    div.className = 'msg assistant';
    div.id = 'streaming-msg';
    div.innerHTML = `
      <div class="msg-role">ASSISTANT</div>
      <div class="msg-body"></div>
    `;
    $messages.appendChild(div);
  }
  return div;
}

function removeStreamingMessage() {
  const streamingMsg = document.getElementById('streaming-msg');
  if (streamingMsg) {
    streamingMsg.remove();
  }
}

/**
 * 通用标签页切换（SKILLS/TOOLS 与 INTELLIGENCE 面板共用）
 */
function switchTab(tabsSelector, contentSelector, tabName) {
  document.querySelectorAll(`${tabsSelector} .tab-btn`).forEach((b) => {
    b.classList.toggle('active', b.dataset.tab === tabName);
  });
  document.querySelectorAll(`${contentSelector} .tab-panel`).forEach((p) => {
    p.classList.toggle('active', p.id === `tab-${tabName}`);
  });
}

function switchIntelligenceTab(tabName) {
  switchTab('.intelligence-tabs', '.intelligence-content', tabName);
}

function switchToolsTab(tabName) {
  switchTab('.tools-tabs', '.tools-content', tabName);
}

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
