/**
 * 上古必斩必杀 初始化和事件绑定
 */

// 初始化聊天
newChat();

// 加载技能和工具
loadSkills();
loadTools();

// 加载热点资讯和告警
loadTrends();
loadAlerts();
loadAlertHistory();

// 加载RSS订阅
loadRssSources();
loadRssArticles();

// 启动告警流监听
startAlertStream();

// 启动RSS流监听
startRssStream();

// 定时刷新待办事项
todoPollInterval = setInterval(loadTodo, POLL_INTERVAL);

// 发送按钮点击事件
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

// 输入框键盘事件
$input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    $send.click();
  }
});

// 输入框自动调整高度
$input.addEventListener('input', () => {
  $input.style.height = 'auto';
  $input.style.height = Math.min($input.scrollHeight, 200) + 'px';
});

// 新建对话按钮
$btnNew.addEventListener('click', () => {
  if (currentAbortController) {
    currentAbortController.abort();
  }
  newChat();
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

// 告警按钮事件
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

// 关联搜索按钮事件
if ($btnSearchLinks) {
  $btnSearchLinks.addEventListener('click', searchLinks);
}
if ($linkKeywordInput) {
  $linkKeywordInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') searchLinks();
  });
}

// 监听窗口大小变化
window.addEventListener('resize', () => {});

// 定期检查输入框状态
setInterval(() => {
  if (!$input.hasAttribute('tabindex')) {
    $input.setAttribute('tabindex', '0');
  }
}, 2000);

// 初始化技能/工具面板标签页切换
document.querySelectorAll('.tools-tabs .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tools-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tools-content .tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.dataset.tab;
    const panel = document.getElementById(`tab-${tabId}`);
    if (panel) panel.classList.add('active');
  });
});

// 初始化INTELLIGENCE面板标签页切换
document.querySelectorAll('.intelligence-tabs .tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.intelligence-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.intelligence-content .tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.dataset.tab;
    const panel = document.getElementById(`tab-${tabId}`);
    if (panel) panel.classList.add('active');
  });
});

// RSS按钮事件
if ($btnAddRss) {
  $btnAddRss.addEventListener('click', () => {
    const url = $rssInput.value.trim();
    if (url) addRssSource(url);
  });
}

if ($rssInput) {
  $rssInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const url = $rssInput.value.trim();
      if (url) addRssSource(url);
    }
  });
}