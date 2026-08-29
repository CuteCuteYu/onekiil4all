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
  setLoading(true, 'processing');
  // Agent 运行中显示 STOP 按钮，隐藏 SEND
  $btnStop.style.display = 'inline-block';
  $send.style.display = 'none';

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
    let segmentBase = 0;
    let metadata = null;

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
              appendProgressMessage(event.message, 'info');
            } else if (event.type === 'todo_created') {
              appendProgressMessage('任务清单已创建', 'success');
              setTimeout(loadTodo, 500);
            } else if (event.type === 'loop_end') {
              // agent loop 结束，展示停止原因
              const reasons = {
                completed: '任务已完成',
                max_iterations: `已达最大迭代次数(${event.iterations}次)`,
                no_next_action: '无下一步操作',
                no_todo: '无任务清单'
              };
              const msg = reasons[event.reason] || '处理完成';
              appendProgressMessage(msg, event.reason === 'completed' ? 'success' : 'info');
            } else if (event.type === 'tool_call') {
              appendProgressMessage(`[工具] ${event.name}: ${event.status}`, 'info');
            } else if (event.type === 'segment_start') {
              // 新的一段AI回复开始（工具调用后的新一轮或自动迭代）
              ensureStreamingMessage();
              segmentBase = messageContent.length;
            } else if (event.type === 'response') {
              // token 增量，流式渲染到固定容器
              const streamEl = ensureStreamingMessage();
              messageContent += event.content;
              renderMarkdown(streamEl.querySelector('.msg-body'), messageContent);
            } else if (event.type === 'response_final') {
              // 本段结束，用后端权威完整文本替换流式内容
              const streamEl = ensureStreamingMessage();
              messageContent = messageContent.slice(0, segmentBase) + event.content;
              renderMarkdown(streamEl.querySelector('.msg-body'), messageContent);
            } else if (event.type === 'done') {
              metadata = event.metadata;
            }
          } catch (e) {}
        }
      }
    }

    removeStreamingMessage();
    if (messageContent) {
      renderMessage('assistant', messageContent, metadata);
    }

  } catch (e) {
    removeStreamingMessage();
    if (e.name === 'AbortError') {
      appendProgressMessage('已中断，任务未完成', 'warning');
    } else {
      console.error('Chat error:', e);
      appendProgressMessage(`错误: ${e.message}`, 'error');
    }
  } finally {
    setBusyState(false);
    setLoading(false);
    currentAbortController = null;
    // 恢复按钮状态：隐藏 STOP，显示 SEND
    $btnStop.style.display = 'none';
    $send.style.display = 'inline-block';

    if (pendingMessages.length > 0 && !busy) {
      const nextMsg = pendingMessages.shift();
      $pendingQueue.classList.add('active');
      renderPendingList();
      await sendMessage(nextMsg);
    } else if (pendingMessages.length === 0) {
      $pendingQueue.classList.remove('active');
    }
  }
}

function addPendingMessage(text) {
  pendingMessages.push(text);
  renderPendingList();
  $pendingQueue.classList.add('active');
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
        $pendingQueue.classList.remove('active');
      }
    });
  });
}

function clearPendingQueue() {
  pendingMessages = [];
  $pendingQueue.classList.remove('active');
}
