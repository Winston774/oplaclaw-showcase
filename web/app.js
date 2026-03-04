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

// ── Fallback Prompt Template ──
function buildFallbackPrompt(v) {
  return `你是一位 AI 代理助手。你的任務是學習以下影片的完整內容，分析使用者當前環境與影片需求的差距，再等待使用者確認後幫助他建立環境並執行任務。

## 影片資訊
- 標題：${v.title}
- 分類：${v.category}
- 摘要：${v.summary || ''}

---

## 第一步：確認 Transcript 技能是否就緒

嘗試使用 youtube-transcript-yt-dlp 技能取得以下影片的英文字幕（含時間戳記）。

**如果技能尚未安裝，請向使用者說明（已安裝者可忽略此段）：**

> 請在終端機執行以下指令安裝字幕技能：
>
> npx clawhub@latest install itzsubhadip/youtube-transcript-yt-dlp
>
> 安裝完成後，重新貼上這段 Prompt 即可繼續。

若技能已就緒，直接進行下一步，不需顯示安裝說明。

---

## 第二步：取得字幕並翻譯分析

成功呼叫技能後：

1. 優先取得**英文字幕**（若無英文字幕，改取任何可用語言）
2. 將逐字稿全文翻譯成**繁體中文**
3. 進行以下分析：

**A. 影片核心能力**
條列 3–5 項「學完後你將能夠⋯⋯」的具體能力

**B. 所需環境與工具清單**
列出影片提到的所有工具、平台、API、套件及版本需求

**C. 環境差距分析**
主動掃描使用者目前的環境（已安裝工具、現有設定），與 B 項清單逐一對照：
- ✅ 已就緒的項目
- ❌ 缺少或需要設定的項目

**D. 建議執行順序**
根據差距分析，列出最短路徑的設定步驟

---

## 第三步：提案並等待確認

完成分析後，向使用者呈現：

「我已讀完這支影片的完整內容。

**學完後你將具備的能力：**
[列出 A]

**環境差距分析：**
[列出 C]

**建議設定步驟：**
[列出 D]

請問要開始嗎？或者告訴我你想從哪個步驟切入。」

---

## 第四步：建立環境並執行任務

使用者確認後，依步驟協助建立環境並執行任務。
遇到需要使用者手動操作的步驟時，暫停說明並等待確認後再繼續。

---

影片來源：${v.url}`;
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
      if (!video) return;
      const text = video.prompts?.length
        ? video.prompts.join('\n\n')
        : buildFallbackPrompt(video);
      navigator.clipboard.writeText(text).then(() => {
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
        <button class="btn-copy" data-id="${v.id}">
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
    const res = await fetch('./data/videos.json');
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
