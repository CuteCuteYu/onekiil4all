/**
 * 上古必斩必杀 关联搜索功能
 */

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