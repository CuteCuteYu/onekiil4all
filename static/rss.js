/**
 * 上古必斩必杀 RSS订阅功能
 */

async function loadRssSources() {
  try {
    const res = await fetch(`${API}/api/rss`);
    const data = await res.json();
    
    if (!data.sources || data.sources.length === 0) {
      $rssSources.innerHTML = '<div class="rss-empty">no sources</div>';
      return;
    }
    
    $rssSources.innerHTML = data.sources.map(source => `
      <div class="rss-source-item ${source.enabled ? '' : 'disabled'}" data-id="${source.id}">
        <span class="rss-source-name" title="${escapeHtml(source.url)}">${escapeHtml(source.name)}</span>
        <div class="rss-source-actions">
          <button class="rss-btn toggle" data-id="${source.id}" title="${source.enabled ? '禁用' : '启用'}">${source.enabled ? 'ON' : 'OFF'}</button>
          <button class="rss-btn delete" data-id="${source.id}" title="删除">DEL</button>
        </div>
      </div>
    `).join('');
    
    $rssSources.querySelectorAll('.rss-btn.toggle').forEach(el => {
      el.addEventListener('click', async (e) => {
        e.stopPropagation();
        const sourceId = el.dataset.id;
        await toggleRssSource(sourceId);
      });
    });
    
    $rssSources.querySelectorAll('.rss-btn.delete').forEach(el => {
      el.addEventListener('click', async (e) => {
        e.stopPropagation();
        const sourceId = el.dataset.id;
        await deleteRssSource(sourceId);
      });
    });
  } catch (e) {
    console.error('Failed to load RSS sources:', e);
    $rssSources.innerHTML = '<div class="rss-empty">load failed</div>';
  }
}

async function addRssSource(url) {
  try {
    const res = await fetch(`${API}/api/rss`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    
    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || '添加失败');
      return;
    }
    
    $rssInput.value = '';
    loadRssSources();
    loadRssArticles();
  } catch (e) {
    console.error('Failed to add RSS source:', e);
    alert('添加失败: ' + e.message);
  }
}

async function toggleRssSource(sourceId) {
  try {
    const res = await fetch(`${API}/api/rss/${sourceId}/toggle`, {
      method: 'POST',
    });
    
    if (res.ok) {
      loadRssSources();
    }
  } catch (e) {
    console.error('Failed to toggle RSS source:', e);
  }
}

async function deleteRssSource(sourceId) {
  try {
    const res = await fetch(`${API}/api/rss/${sourceId}`, {
      method: 'DELETE',
    });
    
    if (res.ok) {
      loadRssSources();
      loadRssArticles();
    }
  } catch (e) {
    console.error('Failed to delete RSS source:', e);
  }
}

async function loadRssArticles() {
  try {
    const res = await fetch(`${API}/api/rss/articles`);
    const data = await res.json();
    
    if (!data.articles || data.articles.length === 0) {
      $rssArticles.innerHTML = '<div class="list-empty">添加订阅源后显示文章</div>';
      return;
    }
    
    $rssArticles.innerHTML = data.articles.map(item => `
      <div class="rss-article-item">
        <div class="rss-article-source">${escapeHtml(item.source)}</div>
        <div class="rss-article-title">
          <a href="${escapeHtml(item.link || '#')}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>
        </div>
        <div class="rss-article-meta">
          <span>${escapeHtml(item.pubDate || '')}</span>
          ${item.description ? `<span class="rss-article-desc">${escapeHtml(item.description)}</span>` : ''}
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load RSS articles:', e);
    $rssArticles.innerHTML = '<div class="list-empty">load failed</div>';
  }
}

function handleNewRss(article) {
  appendProgressMessage(`[RSS] ${article.source}: ${article.title}`, 'info');
  loadRssArticles();
}

let rssEventSource = null;

function startRssStream() {
  if (rssEventSource) {
    rssEventSource.close();
  }
  
  rssEventSource = new EventSource(`${API}/api/rss/stream`);
  
  rssEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'rss' && data.article) {
        handleNewRss(data.article);
      } else if (data.type === 'ping') {
        // heartbeat
      }
    } catch (e) {
      console.error('Failed to parse RSS event:', e);
    }
  };
  
  rssEventSource.onerror = () => {
    console.log('RSS stream connection lost, reconnecting...');
    rssEventSource.close();
    setTimeout(startRssStream, 5000);
  };
}