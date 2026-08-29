/**
 * 上古必斩必杀 热点资讯功能
 */

async function loadTrends() {
  try {
    const res = await fetch(`${API}/api/trends`);
    const data = await res.json();

    const hasRealData =
      data.hot_search &&
      data.hot_search.length > 0 &&
      !(data.hot_search.length === 1 && data.hot_search[0].word === '暂无数据');

    if (hasRealData) {
      const grouped = groupBySource(data.hot_search);
      $hotsearchList.innerHTML = Object.entries(grouped).map(([source, items]) => `
        <div class="trend-group">
          <div class="trend-group-title">${escapeHtml(source)}</div>
          ${items.map(item => renderHotsearchItem(item)).join('')}
        </div>
      `).join('');
    } else {
      $hotsearchList.innerHTML = '<div class="list-loading">no data</div>';
    }
  } catch (e) {
    $hotsearchList.innerHTML = '<div class="list-error">加载失败</div>';
  }
}

function groupBySource(data) {
  const groups = {};
  data.forEach(item => {
    const source = item.source || 'unknown';
    if (!groups[source]) groups[source] = [];
    groups[source].push(item);
  });
  return groups;
}

function formatHot(value) {
  if (value === null || value === undefined || value === '') return '';
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return '';
  if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, '') + '万';
  return String(n);
}

function renderHotsearchItem(item) {
  const hot = formatHot(item.hot);
  return `
    <div class="trend-item">
      <div class="trend-item-title">
        <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener">${escapeHtml(item.word)}</a>
        ${hot ? `<span class="trend-hot">${hot}</span>` : ''}
      </div>
    </div>
  `;
}