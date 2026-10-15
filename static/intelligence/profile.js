/**
 * 上古必斩必杀 消息心理画像功能
 * 粘贴可疑消息样本 → 走 /api/chat（同一线程）→ SSE 流式接收画像报告
 */

// 是否正在分析中
let profileAnalyzing = false;

/**
 * 提交画像分析：把样本包装成指令发给当前会话线程，
 * 结果同时流式渲染到聊天区与 PROFILE 面板。
 */
async function analyzeProfile() {
  const sample = $profileInput.value.trim();
  if (!sample) {
    alert('请先粘贴要分析的消息样本');
    return;
  }
  if (profileAnalyzing || busy) {
    alert('Agent 正在处理中，请稍候');
    return;
  }
  if (!threadId) {
    await newChat();
  }

  profileAnalyzing = true;
  $btnProfileSubmit.disabled = true;
  $btnProfileSubmit.textContent = 'ANALYZING...';
  $profileResult.innerHTML = '<div class="list-loading">正在生成心理画像报告...</div>';

  const prompt = [
    '请对下面的可疑消息样本做社会工程学心理画像分析（只分析、不生成话术），',
    '按 se-psych-profile 技能的画像卡片结构输出（阶段判定/角色原型/杠杆命中/逐句标注/易感性/应对要点/置信度）：',
    '',
    '---消息样本开始---',
    sample,
    '---消息样本结束---',
  ].join('\n');

  try {
    const result = await sendMessage(prompt);
    if (result && result.ok === false) {
      // 后端出错或无内容：展示失败态，不显示“已生成”
      $profileResult.innerHTML = `<div class="list-empty">分析失败：AI 未能生成报告，详见聊天区提示</div>`;
      return;
    }
    // sendMessage 完成后，报告已在聊天区渲染；
    // PROFILE 面板展示提示与入口（报告主体在聊天区，避免双份长文）
    $profileResult.innerHTML = `
      <div class="profile-done">
        <div class="profile-done-title">画像报告已生成</div>
        <div class="profile-done-sub">完整报告见左侧聊天区</div>
        <div class="profile-done-actions">
          <button class="btn-profile-mini" onclick="profileSendToGraph()">沉淀到 CANVAS 图谱</button>
          <button class="btn-profile-mini" onclick="profileFocusChat()">查看报告</button>
        </div>
        <div class="profile-done-hint" id="profile-graph-hint"></div>
      </div>`;
  } catch (e) {
    $profileResult.innerHTML = `<div class="list-empty">分析失败：${escapeHtml(String(e && e.message ? e.message : e))}</div>`;
  } finally {
    profileAnalyzing = false;
    $btnProfileSubmit.disabled = false;
    $btnProfileSubmit.textContent = 'ANALYZE';
  }
}

/** 沉淀到图谱：让 Agent 把最近一次画像结果写入画板（需用户确认，Agent 会请求同意） */
async function profileSendToGraph() {
  const hint = document.getElementById('profile-graph-hint');
  if (busy) {
    alert('Agent 正在处理中，请稍候');
    return;
  }
  const instruction = [
    '请把刚才那份心理画像报告沉淀到情报画板（先 graphrag_status 确认画板已保存；',
    '若未保存或未打开画板，提示我先在 CANVAS 处理后再试）：',
    '- 骗术模式建 FraudPattern 节点',
    '- 每个命中的心理杠杆建 PsychLever 节点，关系 USES',
    '- 话术阶段建 ScriptStage 节点，关系 STAGE',
    '- 冒充角色原型建 Persona 节点，关系 PERSONA',
    '用 graph_add_node / graph_add_edge 写入，完成后告诉我写入了哪些节点和关系。',
  ].join('\n');
  await sendMessage(instruction);
  if (hint) hint.textContent = '已发送入图指令，进展见聊天区；写入后请在 CANVAS 保存画板。';
}

/** 引导用户视线回到聊天区查看报告 */
function profileFocusChat() {
  document.querySelector('.main-content').scrollIntoView({ behavior: 'smooth' });
  $messages.scrollTop = $messages.scrollHeight;
}

// 绑定事件（init.js 之前加载，此处直接绑定）
if ($btnProfileSubmit) {
  $btnProfileSubmit.addEventListener('click', analyzeProfile);
}
if ($btnProfileClear) {
  $btnProfileClear.addEventListener('click', () => {
    $profileInput.value = '';
    $profileInput.style.height = 'auto';
    $profileResult.innerHTML = '<div class="list-empty">粘贴消息后点击 ANALYZE</div>';
  });
}
// Ctrl+Enter 快捷提交
if ($profileInput) {
  $profileInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      analyzeProfile();
    }
  });
}
