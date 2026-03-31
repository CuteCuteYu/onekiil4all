/**
 * 上古必斩必杀 热点资讯功能
 */

async function loadTrends() {
  try {
    const res = await fetch(`${API}/api/trends`);
    const data = await res.json();
    
    const platformMap = {
      hot_search: { list: $hotsearchList, data: data.hot_search, template: renderHotsearchItem },
      github: { list: $githubList, data: data.github, template: renderGithubItem },
      tech: { list: $techList, data: data.tech_news, template: renderTechItem },
    };
    
    for (const [key, conf] of Object.entries(platformMap)) {
      if (conf.data && conf.data.length > 0) {
        const grouped = groupBySource(conf.data);
        conf.list.innerHTML = Object.entries(grouped).map(([source, items]) => `
          <div class="trend-group">
            <div class="trend-group-title">${source}</div>
            ${items.map(item => conf.template(item)).join('')}
          </div>
        `).join('');
      } else {
        conf.list.innerHTML = '<div class="list-loading">no data</div>';
      }
    }
  } catch (e) {
    $hotsearchList.innerHTML = '<div class="list-error">加载失败</div>';
    $githubList.innerHTML = '<div class="list-error">加载失败</div>';
    $techList.innerHTML = '<div class="list-error">加载失败</div>';
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

function renderHotsearchItem(item) {
  return `
    <div class="trend-item">
      <div class="trend-item-title">
        <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener">${escapeHtml(item.word)}</a>
      </div>
    </div>
  `;
}

function renderGithubItem(item) {
  return `
    <div class="trend-item">
      <div class="trend-item-title">
        <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener">${escapeHtml(item.name)}</a>
      </div>
      <div class="trend-item-desc">${escapeHtml(item.description || '')}</div>
    </div>
  `;
}

function renderTechItem(item) {
  return `
    <div class="trend-item">
      <div class="trend-item-title">
        <a href="${escapeHtml(item.url || '#')}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>
      </div>
    </div>
  `;
}