// ── State ──
let allVideos = [];
let activeCategory = 'All';
let searchQuery = '';

// ── Chart ──
function renderChart(videos) {
  const counts = {};
  videos.forEach(v => { counts[v.category] = (counts[v.category] || 0) + 1; });
  const labels = Object.keys(counts);
  const values = Object.values(counts);

  const COLORS = [
    '#f97316', '#fb923c', '#fbbf24', '#4ade80',
    '#34d399', '#22d3ee', '#818cf8', '#c084fc', '#f472b6'
  ];

  const ctx = document.getElementById('donut-chart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: COLORS.slice(0, labels.length),
        borderColor: '#0d0d0d',
        borderWidth: 3,
        hoverOffset: 6,
      }]
    },
    options: {
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw} 個`
          }
        }
      }
    }
  });
}

// ── Stats ──
function renderStats(data) {
  const total = data.total || data.videos.length;
  const cats = new Set(data.videos.map(v => v.category)).size;

  document.getElementById('nav-count').textContent = `${total} RESULTS`;
  document.getElementById('hero-count').textContent = total;
  document.getElementById('stat-total').textContent = total;
  document.getElementById('stat-cats').textContent = cats;
}

// ── Filters ──
function renderFilters() {
  const cats = ['All', ...new Set(allVideos.map(v => v.category))];
  const container = document.getElementById('filter-pills');
  container.innerHTML = cats.map(cat => `
    <button class="pill ${cat === 'All' ? 'active' : ''}" data-cat="${cat}">
      ${cat === 'All' ? '' : (allVideos.find(v => v.category === cat)?.category_icon || '') + ' '}${cat}
    </button>
  `).join('');

  container.querySelectorAll('.pill').forEach(pill => {
    pill.addEventListener('click', () => {
      activeCategory = pill.dataset.cat;
      container.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      renderCards();
    });
  });
}

// ── Cards ──
function getFiltered() {
  return allVideos.filter(v => {
    const matchCat = activeCategory === 'All' || v.category === activeCategory;
    const matchSearch = !searchQuery ||
      v.title.toLowerCase().includes(searchQuery) ||
      (v.summary || '').toLowerCase().includes(searchQuery) ||
      (v.tags || []).some(t => t.toLowerCase().includes(searchQuery));
    return matchCat && matchSearch;
  });
}

function renderCards() {
  const videos = getFiltered();
  const grid = document.getElementById('card-grid');
  const noResults = document.getElementById('no-results');

  if (videos.length === 0) {
    grid.innerHTML = '';
    noResults.style.display = 'block';
    return;
  }

  noResults.style.display = 'none';
  grid.innerHTML = videos.map(v => renderCard(v)).join('');

  // Bind copy buttons
  grid.querySelectorAll('.btn-copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.id;
      const video = allVideos.find(v => v.id === id);
      if (!video || !video.prompts?.length) return;
      navigator.clipboard.writeText(video.prompts.join('\n\n')).then(() => {
        btn.textContent = '✓ 已複製';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.innerHTML = '📋 Copy Prompt';
          btn.classList.remove('copied');
        }, 2000);
      });
    });
  });
}

function renderCard(v) {
  const hasPrompts = v.prompts && v.prompts.length > 0;

  // Safe title highlight — escape special regex chars before replace
  let titleHtml = v.title;
  if (v.title_highlight) {
    const escaped = v.title_highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    titleHtml = v.title.replace(new RegExp(escaped, 'i'), match =>
      `<span class="highlight">${match}</span>`
    );
  }

  const tagsHtml = (v.tags || []).map(t => `<span class="tag">${t}</span>`).join('');

  return `
    <div class="card">
      <div class="card-top">
        <div class="card-category">
          <span class="cat-icon">${v.category_icon || '📌'}</span>
          ${v.category}
        </div>
        <a href="${v.url}" target="_blank" class="card-play-icon" title="在 YouTube 觀看">▶</a>
      </div>
      <div class="card-title">${titleHtml}</div>
      <div class="card-summary">${v.summary || ''}</div>
      ${tagsHtml ? `<div class="card-tags">${tagsHtml}</div>` : ''}
      <div class="card-actions">
        <button class="btn-copy" data-id="${v.id}" ${!hasPrompts ? 'disabled title="此影片無提示詞"' : ''}>
          📋 Copy Prompt
        </button>
        <a href="${v.url}" target="_blank" class="btn-watch">
          ▶ ${v.duration || 'Watch'}
        </a>
      </div>
    </div>
  `;
}

// ── Init ──
async function init() {
  try {
    const res = await fetch('../data/videos.json');
    if (!res.ok) throw new Error('Failed to load videos.json');
    const data = await res.json();
    allVideos = data.videos || [];
    renderStats(data);
    renderChart(data.videos);
    renderFilters();
    renderCards();
  } catch (e) {
    document.getElementById('card-grid').innerHTML =
      `<div class="loading">⚠️ 無法載入資料：${e.message}<br><small>請先執行 python fetch.py</small></div>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('search-input').addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase();
    renderCards();
  });
  init();
});
