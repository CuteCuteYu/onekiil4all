/**
 * 上古必斩必杀 告警详情页面脚本
 * 负责处理告警时间线和详情展示
 */

const API = '';
const urlParams = new URLSearchParams(window.location.search);
const keyword = urlParams.get('keyword') || '';

let timelineData = [];
let filteredData = [];

const $keywordValue = document.getElementById('keyword-value');
const $totalEvents = document.getElementById('total-events');
const $timelineList = document.getElementById('timeline-list');
const $detailView = document.getElementById('detail-view');
const $searchInput = document.getElementById('search-input');
const $btnBack = document.getElementById('btn-back');
const $btnHome = document.getElementById('btn-home');

const $infoKeyword = document.getElementById('info-keyword');
const $infoCreated = document.getElementById('info-created');
const $infoTotal = document.getElementById('info-total');
const $countHotsearch = document.getElementById('count-hotsearch');
const $countGithub = document.getElementById('count-github');
const $countTech = document.getElementById('count-tech');

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function formatTime(isoString) {
  if (!isoString) return '--';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatFullTime(isoString) {
  if (!isoString) return '--';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

async function loadTimeline() {
  if (!keyword) {
    $timelineList.innerHTML = '<div class="list-empty">no keyword specified</div>';
    return;
  }

  try {
    const res = await fetch(`${API}/api/alerts/timeline/${encodeURIComponent(keyword)}`);
    const data = await res.json();

    timelineData = data.timeline || [];
    filteredData = [...timelineData];

    renderKeyword();
    renderStats();
    renderTimeline();
    renderInfo();
  } catch (e) {
    console.error('Failed to load timeline:', e);
    $timelineList.innerHTML = '<div class="list-empty">load failed</div>';
  }
}

function renderKeyword() {
  $keywordValue.textContent = keyword;
}

function renderStats() {
  $totalEvents.textContent = timelineData.length;
}

function renderTimeline() {
  if (filteredData.length === 0) {
    $timelineList.innerHTML = '<div class="list-empty">no events</div>';
    return;
  }

  $timelineList.innerHTML = filteredData.map((item, index) => `
    <div class="timeline-item" data-index="${index}" data-id="${item.id}">
      <div class="timeline-time">${formatTime(item.triggered_at)}</div>
      <div class="timeline-title">${escapeHtml(item.title)}</div>
      <span class="timeline-source">${escapeHtml(item.source || item.type)}</span>
    </div>
  `).join('');

  $timelineList.querySelectorAll('.timeline-item').forEach(el => {
    el.addEventListener('click', () => {
      const index = parseInt(el.dataset.index);
      showDetail(index);
    });
  });
}

function renderInfo() {
  $infoKeyword.textContent = keyword;
  $infoCreated.textContent = formatTime(timelineData[0]?.triggered_at || '');
  $infoTotal.textContent = timelineData.length;

  const counts = { hotsearch: 0, github: 0, tech_news: 0 };
  timelineData.forEach(item => {
    const type = item.type || 'hotsearch';
    if (counts.hasOwnProperty(type)) {
      counts[type]++;
    }
  });

  $countHotsearch.textContent = counts.hotsearch;
  $countGithub.textContent = counts.github;
  $countTech.textContent = counts.tech_news;
}

function showDetail(index) {
  const item = filteredData[index];
  if (!item) return;

  $timelineList.querySelectorAll('.timeline-item').forEach(el => {
    el.classList.remove('active');
    if (parseInt(el.dataset.index) === index) {
      el.classList.add('active');
    }
  });

  const sourceLabel = item.source || item.type || 'unknown';

  $detailView.innerHTML = `
    <div class="detail-content active">
      <div class="detail-header">
        <div class="detail-title">${escapeHtml(item.title)}</div>
        <div class="detail-meta">
          <span>${formatFullTime(item.triggered_at)}</span>
          <span>${escapeHtml(sourceLabel)}</span>
        </div>
      </div>
      <div class="detail-body">
        <div class="detail-section">
          <div class="detail-section-title">KEYWORD</div>
          <div>${escapeHtml(item.keyword)}</div>
        </div>
        <div class="detail-section">
          <div class="detail-section-title">SOURCE</div>
          <div>${escapeHtml(item.source || 'unknown')}</div>
        </div>
        ${item.url ? `
        <div class="detail-section">
          <div class="detail-section-title">LINK</div>
          <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener" class="detail-link">
            OPEN ${escapeHtml(item.url)}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </a>
        </div>
        ` : ''}
      </div>
    </div>
  `;
}

function filterTimeline(searchTerm) {
  if (!searchTerm) {
    filteredData = [...timelineData];
  } else {
    const term = searchTerm.toLowerCase();
    filteredData = timelineData.filter(item => 
      item.title.toLowerCase().includes(term) ||
      item.keyword.toLowerCase().includes(term) ||
      item.source.toLowerCase().includes(term)
    );
  }
  renderTimeline();
}

$searchInput.addEventListener('input', (e) => {
  filterTimeline(e.target.value);
});

$btnBack.addEventListener('click', () => {
  window.location.href = '/';
});

loadTimeline();
