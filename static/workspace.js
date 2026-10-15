/**
 * 上古必斩必杀 工作区选择
 * 初始化时必须先选择一个文件夹作为工作区，Agent 产物默认保存在该文件夹
 */

const $wsOverlay = document.getElementById('workspace-overlay');
const $wsInput = document.getElementById('workspace-input');
const $wsBrowse = document.getElementById('workspace-browse');
const $wsError = document.getElementById('workspace-error');
const $wsConfirm = document.getElementById('workspace-confirm');
const $wsBadge = document.getElementById('workspace-badge');

// 当前工作区路径（null 表示未选择）
let workspacePath = null;

/** 显示工作区错误提示 */
function showWorkspaceError(msg) {
  $wsError.textContent = msg;
  $wsError.hidden = false;
}

/** 隐藏工作区错误提示 */
function hideWorkspaceError() {
  $wsError.textContent = '';
  $wsError.hidden = true;
}

/** 打开工作区选择遮罩（预填当前路径，方便微调） */
function openWorkspacePicker() {
  if (workspacePath) $wsInput.value = workspacePath;
  hideWorkspaceError();
  $wsOverlay.hidden = false;
  $wsInput.focus();
}

/** 关闭工作区选择遮罩 */
function closeWorkspacePicker() {
  $wsOverlay.hidden = true;
}

/** 更新页头工作区徽章显示 */
function renderWorkspaceBadge() {
  if (!workspacePath) {
    $wsBadge.hidden = true;
    return;
  }
  // 显示最后一段目录名，完整路径放在 title 里
  const name = workspacePath.replace(/[\\/]+$/, '').split(/[\\/]/).pop() || workspacePath;
  $wsBadge.textContent = `➋ ${name}`;
  $wsBadge.title = `工作区：${workspacePath}（点击切换）`;
  $wsBadge.hidden = false;
}

/** 提交工作区路径：校验成功后关闭遮罩并恢复聊天 */
async function confirmWorkspace() {
  const path = $wsInput.value.trim();
  if (!path) {
    showWorkspaceError('请输入文件夹路径');
    return;
  }
  $wsConfirm.disabled = true;
  $wsConfirm.textContent = '验证中...';
  hideWorkspaceError();
  try {
    const res = await fetch(`${API}/api/workspace`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    const data = await res.json();
    if (!res.ok) {
      showWorkspaceError(data.detail || '路径无效，请确认文件夹存在');
      return;
    }
    workspacePath = data.workspace;
    renderWorkspaceBadge();
    closeWorkspacePicker();
  } catch (e) {
    showWorkspaceError(`连接失败: ${e.message}`);
  } finally {
    $wsConfirm.disabled = false;
    $wsConfirm.textContent = '进入工作区';
  }
}

/** 初始化：查询后端工作区状态，未选择则弹遮罩阻断使用 */
async function initWorkspace() {
  try {
    const res = await fetch(`${API}/api/workspace`);
    const data = await res.json();
    if (data.ready && data.workspace) {
      workspacePath = data.workspace;
      renderWorkspaceBadge();
      return;
    }
  } catch (e) {
    console.error('Failed to query workspace:', e);
  }
  // 未选择工作区：显示选择页，阻断 Agent loop
  openWorkspacePicker();
}

// 徽章点击重新选择工作区
$wsBadge.addEventListener('click', openWorkspacePicker);

// 确认按钮
$wsConfirm.addEventListener('click', confirmWorkspace);

// 输入框回车提交
$wsInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    confirmWorkspace();
  }
});

// 浏览按钮：通过 Web目录 API 探测常见根路径提示，主要仍靠手动输入
$wsBrowse.addEventListener('click', () => {
  $wsInput.focus();
  const current = $wsInput.value.trim();
  const guess = current || 'D:\\workspace';
  $wsInput.value = guess;
});
