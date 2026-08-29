/**
 * 上古必斩必杀 关联搜索功能
 */

// 搜索防抖:相同关键词在途请求直接复用,避免重复外呼
let _linkSearching = false;

async function searchLinks() {
  const keyword = $linkKeywordInput.value.trim();

  if (!keyword || keyword.length < 2) {
    $linkResults.innerHTML = '<div class="list-empty">请输入至少2个字符的关键词</div>';
    return;
  }

  if (_linkSearching) return;
  _linkSearching = true;
  $linkResults.innerHTML = '<div class="list-loading">正在搜索并分析相关关键词...</div>';

  try {
    const res = await fetch(
      API + '/api/trends/associations?keyword=' + encodeURIComponent(keyword)
    );
    const data = await res.json();

    if (data.error) {
      $linkResults.innerHTML = '<div class="list-empty">' + escapeHtml(data.error) + '</div>';
      return;
    }

    renderLinkResults(data);
  } catch (e) {
    console.error('Failed to search links:', e);
    $linkResults.innerHTML = '<div class="list-empty">load failed</div>';
  } finally {
    _linkSearching = false;
  }
}

function renderLinkResults(data) {
  const items = data.associations || [];

  if (items.length === 0) {
    $linkResults.innerHTML = '<div class="list-empty">未找到相关关键词，试试换个词</div>';
    return;
  }

  const summary =
    '<div class="link-summary">' +
      '<span>共 ' + (data.total != null ? data.total : items.length) + ' 个关联词</span>' +
      '<span class="link-summary-hint">点击词条直接添加告警</span>' +
    '</div>';

  $linkResults.innerHTML = summary + items.map(item =>
    '<div class="link-result-item" data-keyword="' + escapeHtml(item.keyword) + '">' +
      '<span class="kw-name">' + escapeHtml(item.keyword) + '</span>' +
      '<span class="kw-score">' + Math.round(item.score * 100) + '%</span>' +
    '</div>'
  ).join('');

  $linkResults.querySelectorAll('.link-result-item').forEach(el => {
    el.addEventListener('click', async () => {
      const keyword = el.dataset.keyword;
      await addAlertFromLink(keyword);
    });
  });
}

/** 将关联词一键添加为告警规则,带成功/失败反馈 */
async function addAlertFromLink(keyword) {
  try {
    const res = await fetch(API + '/api/alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword }),
    });

    if (!res.ok) {
      // 重复词或失败:给出明确提示
      let detail = '添加失败';
      try { detail = (await res.json()).detail || detail; } catch (e) {}
      alert(detail);
      return;
    }

    const data = await res.json();
    // 切到 ALERTS 标签并高亮新规则(便于确认添加结果)
    switchIntelligenceTab('alerts');
    if (data.alert && window.highlightAlertItem) {
      highlightAlertItem(data.alert.id);
    }
  } catch (e) {
    console.error('Failed to add link alert:', e);
    alert('添加失败: ' + e.message);
  }
}

function clearLinkResults() {
  $linkKeywordInput.value = '';
  $linkResults.innerHTML = '<div class="list-empty">输入关键词查看关联</div>';
}