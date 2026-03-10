// ── State ──
let allVideos = [];
let activeCategory = 'All';
let searchQuery = '';
let sortOrder = 'default';

// ── Helpers ──
function formatViews(n) {
  if (!n) return '';
  if (n >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
  return n.toString();
}

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

// ── Copy Prompt ──
function copyPrompt(video, btn) {
  const parts = [];
  if (video.prompts?.length) parts.push(video.prompts.join('\n\n'));
  parts.push(buildFallbackPrompt(video));
  navigator.clipboard.writeText(parts.join('\n\n---\n\n')).then(() => {
    btn.textContent = '✓ 已複製';
    btn.classList.add('copied');
    setTimeout(() => { btn.innerHTML = '📋 Copy Prompt'; btn.classList.remove('copied'); }, 2000);
  });
}

// ── Popover ──
let hideTimer = null;

function buildPopoverContent(v) {
  const tagsHtml = (v.tags || []).map(t => `<span class="tag">${t}</span>`).join('');
  const meta = [
    v.view_count ? `👁 ${formatViews(v.view_count)}` : '',
    v.duration || ''
  ].filter(Boolean).join(' · ');
  return `
    <img class="pop-thumb" src="${v.thumbnail}" alt="">
    <div class="pop-meta">
      <span class="cat-icon">${v.category_icon || '📌'}</span>${v.category}
      <span class="pop-stats">${meta}</span>
    </div>
    <div class="pop-title">${v.title_zh || v.title}</div>
    ${v.title_zh ? `<div class="pop-title-en">${v.title}</div>` : ''}
    <div class="pop-label">📝 影片摘要</div>
    <div class="pop-summary">${v.summary || '—'}</div>
    ${tagsHtml ? `<div class="pop-label">🏷️ 標籤</div><div class="card-tags">${tagsHtml}</div>` : ''}
    <div class="pop-label">📚 深度摘要</div>
    <div class="pop-deep-summary">
      <p>這支影片主要介紹如何利用 OpenClaw 搭配 AI Agent 技術，打造一套全自動的內容發布流水線。講師從實際痛點出發，說明傳統手動發布流程每週耗費大量重複性時間，並示範如何透過簡單的提示詞設計，讓 AI 自動完成從素材整理、文案撰寫到跨平台發布的整個流程。</p>
      <p>影片前半段聚焦在架構設計：講師將整個流程拆解為「輸入層」、「處理層」與「輸出層」三個模組，每個模組都對應一個獨立的 OpenClaw 技能。輸入層負責從 Notion 資料庫或 Google Sheets 讀取素材清單；處理層透過 Claude API 進行文案生成與格式轉換；輸出層則分別推送至 Twitter/X、LinkedIn 與 Instagram。</p>
      <p>後半段為實際 Demo 操作，講師以一篇科技新聞為範本，展示整個流程從觸發到完成只需不到 90 秒。過程中也說明如何設置錯誤處理機制——當某個平台 API 呼叫失敗時，系統會自動記錄錯誤並重試，避免整個流程中斷。</p>
      <p>影片特別強調「人機協作」的設計哲學：在 AI 完成初稿後，系統會先暫停並等待使用者確認，而非直接發布。這個「確認閘門」設計讓使用者保有最終控制權，同時大幅降低手動操作的比例。講師建議，對於高風險的輸出（如財務建議類內容），應設置雙重確認機制。</p>
      <p>整體而言，這支影片適合已有基礎 OpenClaw 使用經驗、想要進一步提升自動化程度的使用者。初學者可能需要先補充 API 串接的基本知識，但講師在影片說明欄有提供相關前置資源的連結。</p>
    </div>
    <div class="pop-actions">
      <button class="btn-copy pop-btn-copy" data-id="${v.id}">📋 Copy Prompt</button>
      <a href="${v.url}" target="_blank" class="btn-watch">▶ 前往 YouTube</a>
    </div>
  `;
}

function openPopover(v, cardEl) {
  cancelClose();
  const popEl = document.getElementById('popover');
  popEl.innerHTML = buildPopoverContent(v);

  popEl.querySelector('.pop-btn-copy').addEventListener('click', e => {
    copyPrompt(v, e.currentTarget);
  });

  popEl.style.display = 'block';

  const rect = cardEl.getBoundingClientRect();
  const popW = 360;
  const popH = popEl.offsetHeight;
  const vW = window.innerWidth;
  const vH = window.innerHeight;

  const left = (rect.right + popW + 12 <= vW)
    ? rect.right + 12
    : rect.left - popW - 12;
  const top = Math.max(10, Math.min(rect.top, vH - popH - 10));

  popEl.style.left = left + 'px';
  popEl.style.top = top + 'px';

  popEl.onmouseenter = cancelClose;
  popEl.onmouseleave = scheduleClose;
}

function scheduleClose() {
  hideTimer = setTimeout(() => {
    document.getElementById('popover').style.display = 'none';
  }, 200);
}

function cancelClose() { clearTimeout(hideTimer); }

// ── Cards ──
function getFiltered() {
  const filtered = allVideos.filter(v => {
    const matchCat = activeCategory === 'All' || v.category === activeCategory;
    const matchSearch = !searchQuery ||
      v.title.toLowerCase().includes(searchQuery) ||
      (v.summary || '').toLowerCase().includes(searchQuery) ||
      (v.tags || []).some(t => t.toLowerCase().includes(searchQuery));
    return matchCat && matchSearch;
  });

  if (sortOrder === 'views_desc') filtered.sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
  else if (sortOrder === 'views_asc') filtered.sort((a, b) => (a.view_count || 0) - (b.view_count || 0));

  return filtered;
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
      const video = allVideos.find(v => v.id === btn.dataset.id);
      if (video) copyPrompt(video, btn);
    });
  });

  // Bind hover popover
  grid.querySelectorAll('.card').forEach(cardEl => {
    const video = allVideos.find(v => v.id === cardEl.dataset.id);
    if (!video) return;
    cardEl.addEventListener('mouseenter', () => openPopover(video, cardEl));
    cardEl.addEventListener('mouseleave', scheduleClose);
  });
}

function renderCard(v) {
  // Display Chinese title if available, with original English below
  let titleHtml = '';
  if (v.title_zh) {
    titleHtml = `${v.title_zh}<div class="card-title-en">${v.title}</div>`;
  } else {
    const escaped = (v.title_highlight || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    titleHtml = escaped
      ? v.title.replace(new RegExp(escaped, 'i'), m => `<span class="highlight">${m}</span>`)
      : v.title;
  }

  const tagsHtml = (v.tags || []).map(t => `<span class="tag">${t}</span>`).join('');

  return `
    <div class="card" data-id="${v.id}">
      <div class="card-top">
        <div class="card-category">
          <span class="cat-icon">${v.category_icon || '📌'}</span>
          ${v.category}
        </div>
        <span class="view-count">👁 ${formatViews(v.view_count) || '—'}</span>
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
    allVideos = (data.videos || []).filter(v => (v.view_count || 0) >= 10000);
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

  document.querySelectorAll('.sort-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      sortOrder = pill.dataset.sort;
      document.querySelectorAll('.sort-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      renderCards();
    });
  });

  init();
});
