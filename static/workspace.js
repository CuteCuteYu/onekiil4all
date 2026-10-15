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

/** 初始化：同步后端工作区状态到本地（徽章 + workspacePath 缓存） */
async function initWorkspace() {
  try {
    const res = await fetch(`${API}/api/workspace`);
    const data = await res.json();
    if (data.ready && data.workspace) {
      workspacePath = data.workspace;
      renderWorkspaceBadge();
    }
  } catch (e) {
    console.error('Failed to query workspace:', e);
  }
}

/**
 * 新会话要求选择工作区：
 * thread 标识重新生成（首次进入 / 点击 NEW）时调用，
 * 同步服务端状态后弹出选择页（预填当前路径，用户确认后才可继续）。
 */
async function requireWorkspaceForSession() {
  await initWorkspace();
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

// 浏览按钮：请求后端弹出系统原生文件夹选择框，选中即回填路径
$wsBrowse.addEventListener('click', async () => {
  const original = $wsBrowse.textContent;
  $wsBrowse.disabled = true;
  $wsBrowse.textContent = '...';
  try {
    const res = await fetch(`${API}/api/workspace/browse`);
    const data = await res.json();
    if (res.ok && data.path) {
      $wsInput.value = data.path;
      hideWorkspaceError();
      $wsConfirm.focus();
    } else if (res.status === 501) {
      showWorkspaceError(data.detail || '当前环境不支持图形选择，请手动输入路径');
    }
    // 用户取消对话框时保持输入框不变
  } catch (e) {
    showWorkspaceError(`连接失败: ${e.message}`);
  } finally {
    $wsBrowse.disabled = false;
    $wsBrowse.textContent = original;
  }
});
