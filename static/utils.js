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
  if (on) {
    busy = true;
    $send.disabled = true;
    $send.classList.add('busy');
  } else {
    busy = false;
    $send.disabled = false;
    $send.classList.remove('busy');
  }
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

function renderMessage(role, content, metadata = null) {
  removeEmptyState();
  
  const isUser = role === 'user';
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  
  let bodyContent;
  if (isUser) {
    bodyContent = escapeHtml(content);
  } else {
    bodyContent = marked.parse(content);
  }
  
  div.innerHTML = `
    <div class="msg-role">${role.toUpperCase()}</div>
    <div class="msg-body">${bodyContent}</div>
  `;
  
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
  
  div.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });
  
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

function switchIntelligenceTab(tabName) {
  document.querySelectorAll('.intelligence-tabs .tab-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabName);
  });
  document.querySelectorAll('.intelligence-content .tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabName}`);
  });
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