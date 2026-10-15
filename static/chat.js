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

  // 工作区门槛：未选择工作区时引导用户先选择，不进入 Agent loop
  if (!workspacePath) {
    appendProgressMessage('请先选择工作区文件夹，Agent 产物将保存在该文件夹中', 'info');
    openWorkspacePicker();
    // 把被拦截的消息放回输入框，选完工作区后可直接重发
    $input.value = text;
    return;
  }

  setBusyState(true);
  setLoading(true, 'processing');
  // Agent 运行中显示 STOP 按钮，隐藏 SEND
  $btnStop.style.display = 'inline-block';
  $send.style.display = 'none';

  renderMessage('user', text);

  // 状态提升到 try 外，供 catch/finally 与返回值使用
  let messageContent = '';
  let hadError = false;

  try {
    const controller = new AbortController();
    currentAbortController = controller;

    const response = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, thread_id: threadId }),
      signal: controller.signal,
    });

    if (!response.ok) {
      // 409 = 未选择工作区：读取 detail 并弹选择页
      if (response.status === 409) {
        let detail = '尚未选择工作区';
        try {
          const err = await response.json();
          detail = err.detail || detail;
        } catch (_) { /* 忽略解析失败 */ }
        appendProgressMessage(detail, 'error');
        openWorkspacePicker();
        throw new Error(detail);
      }
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
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
                no_progress: '未检测到进展，已停止',
                no_todo: '无任务清单'
              };
              const msg = reasons[event.reason] || '处理完成';
              appendProgressMessage(msg, event.reason === 'completed' ? 'success' : 'info');
            } else if (event.type === 'tool_call') {
              const level = event.status && event.status.startsWith('✗') ? 'error' : 'info';
              appendProgressMessage(`[工具] ${event.name}: ${event.status}`, level);
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
            } else if (event.type === 'error') {
              // 后端错误（401/超时等）必须显式展示，否则用户会以为“完全没反应”
              hadError = true;
              appendProgressMessage(`错误: ${event.message || '未知错误'}`, 'error');
            } else if (event.type === 'note') {
              appendProgressMessage(event.content, 'success');
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
    } else if (!hadError) {
      // 没有任何回复也没有报错时，给出明确提示而不是默默什么都不显示
      appendProgressMessage('模型未返回任何内容，请检查模型配置或稍后重试', 'warning');
    }

  } catch (e) {
    removeStreamingMessage();
    if (e.name === 'AbortError') {
      appendProgressMessage('已中断，任务未完成', 'warning');
    } else {
      console.error('Chat error:', e);
      appendProgressMessage(`错误: ${e.message}`, 'error');
    }
    // 出错时记录失败标志，最终返回给调用方（如 PROFILE 面板）感知失败
    hadError = true;
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

  // 返回执行状态，供调用方（PROFILE 面板等）区分成功/失败
  return { ok: !hadError && !!messageContent, content: messageContent };
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
