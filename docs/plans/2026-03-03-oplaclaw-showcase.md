# OplacLaw YouTube Showcase Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a static website that fetches oplaclaw YouTube videos via API, enriches them with Claude AI (category/summary/prompts), stores them in JSON, and renders a dark-themed filterable card gallery.

**Architecture:** Python CLI script (`fetch.py`) pulls YouTube Data API v3, sends each video to Claude API for enrichment, writes `data/videos.json`. Pure frontend (`index.html` + `style.css` + `app.js`) reads the JSON and renders cards with Chart.js donut chart, category filters, and search.

**Tech Stack:** Python 3.11+, `google-api-python-client`, `anthropic`, `python-dotenv`, vanilla HTML/CSS/JS, Chart.js (CDN)

---

## Task 1: Project scaffold + git init

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `.env.example`

**Step 1: Init git and create directory structure**

```bash
cd /Users/winstonhuang/Youtube_Claw
git init
mkdir -p data web docs/plans
```

**Step 2: Create `.gitignore`**

```
.env
data/videos.json
__pycache__/
*.pyc
.DS_Store
venv/
```

**Step 3: Create `.env.example`**

```
YOUTUBE_API_KEY=your_youtube_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CHANNEL_HANDLE=@oplaclaw
```

**Step 4: Create `README.md`**

```markdown
# OplacLaw YouTube Showcase

展示 oplaclaw YouTube 頻道影片的靜態網站。

## Setup

1. Copy `.env.example` to `.env` and fill in API keys
2. `pip install -r requirements.txt`
3. `python fetch.py` — fetches videos and generates `data/videos.json`
4. Open `web/index.html` in browser

## Getting API Keys

- YouTube Data API v3: https://console.cloud.google.com/
- Anthropic API: https://console.anthropic.com/
```

**Step 5: Commit**

```bash
git add .gitignore README.md .env.example docs/
git commit -m "chore: initial project scaffold"
```

---

## Task 2: Python config + requirements

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `.env` (from .env.example, NOT committed)

**Step 1: Create `requirements.txt`**

```
google-api-python-client==2.115.0
anthropic==0.40.0
python-dotenv==1.0.1
```

**Step 2: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

**Step 3: Create `config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "@oplaclaw")

CATEGORIES = [
    "OpenClaw Setup",
    "內容行銷",
    "生產力",
    "金融",
    "程式開發",
    "個人成長",
    "生活管理",
    "其他",
]

CATEGORY_ICONS = {
    "OpenClaw Setup": "⚙️",
    "內容行銷": "📢",
    "生產力": "⚡",
    "金融": "💰",
    "程式開發": "</>",
    "個人成長": "🌱",
    "生活管理": "🏠",
    "其他": "📌",
}

DATA_FILE = "data/videos.json"
```

**Step 4: Create `.env` with real keys**

Copy `.env.example` to `.env` and fill in:
- `YOUTUBE_API_KEY` — from Google Cloud Console (enable YouTube Data API v3)
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `CHANNEL_HANDLE` — leave as `@oplaclaw`

**Step 5: Commit**

```bash
git add requirements.txt config.py .env.example
git commit -m "chore: add config and dependencies"
```

---

## Task 3: fetch.py — YouTube API integration

**Files:**
- Create: `fetch.py`

**Step 1: Write `fetch.py` with YouTube fetch function**

```python
#!/usr/bin/env python3
"""Fetch oplaclaw YouTube videos and enrich with Claude AI."""

import json
import os
from datetime import datetime

from googleapiclient.discovery import build

from config import YOUTUBE_API_KEY, CHANNEL_HANDLE, DATA_FILE


def get_channel_id(youtube, handle: str) -> str:
    """Resolve @handle to channel ID."""
    response = youtube.search().list(
        part="snippet",
        q=handle,
        type="channel",
        maxResults=1,
    ).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {handle}")
    return items[0]["snippet"]["channelId"]


def fetch_all_videos(youtube, channel_id: str) -> list[dict]:
    """Fetch all public videos from a channel."""
    videos = []
    page_token = None

    while True:
        response = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            type="video",
            order="date",
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            vid_id = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "id": vid_id,
                "title": snippet["title"],
                "description": snippet["description"],
                "published_at": snippet["publishedAt"][:10],
                "thumbnail": snippet["thumbnails"].get("high", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return videos


def fetch_video_durations(youtube, video_ids: list[str]) -> dict[str, str]:
    """Fetch duration for a list of video IDs. Returns {id: "MM:SS"}."""
    durations = {}
    # API allows max 50 IDs per request
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        response = youtube.videos().list(
            part="contentDetails",
            id=",".join(batch),
        ).execute()
        for item in response.get("items", []):
            raw = item["contentDetails"]["duration"]  # e.g. "PT8M5S"
            durations[item["id"]] = _parse_duration(raw)
    return durations


def _parse_duration(iso: str) -> str:
    """Convert PT8M5S → '8:05'."""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return "0:00"
    hours, minutes, seconds = (int(x or 0) for x in m.groups())
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
```

**Step 2: Quick smoke test — verify YouTube API works**

Add this at the bottom of `fetch.py` temporarily:

```python
if __name__ == "__main__":
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    channel_id = get_channel_id(youtube, CHANNEL_HANDLE)
    print(f"Channel ID: {channel_id}")
```

Run: `python fetch.py`
Expected: prints the oplaclaw channel ID (starts with `UC`). Copy this ID — you'll hardcode it in config.py for reliability.

**Step 3: Hardcode channel ID in config.py**

After confirming the channel ID, add to `config.py`:

```python
CHANNEL_ID = "UC..."  # replace with actual ID from step 2
```

---

## Task 4: fetch.py — Claude AI enrichment

**Files:**
- Modify: `fetch.py`

**Step 1: Add Claude enrichment function to `fetch.py`**

```python
import anthropic as anthropic_sdk
from config import ANTHROPIC_API_KEY, CATEGORIES, CATEGORY_ICONS


def enrich_video(client: anthropic_sdk.Anthropic, video: dict) -> dict:
    """Send video title+description to Claude, get category/summary/tags/prompts."""
    categories_str = ", ".join(CATEGORIES)
    prompt = f"""你是一個影片分析助手。根據以下 YouTube 影片資訊，以 JSON 格式回傳分析結果。

影片標題：{video['title']}

影片說明：{video['description'][:1000]}

請回傳以下 JSON（不要加任何其他文字）：
{{
  "category": "從以下選一個: {categories_str}",
  "title_highlight": "標題中最重要的 2-4 個關鍵動作字詞（中文或英文）",
  "summary": "100字以內的繁體中文摘要，說明這部影片教什麼",
  "tags": ["關鍵字1", "關鍵字2", "關鍵字3"],
  "prompts": ["設定此功能所需的完整 AI 指令（若影片有提到的話，否則空陣列）"]
}}"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw)

    # Validate category
    if result.get("category") not in CATEGORIES:
        result["category"] = "其他"

    result["category_icon"] = CATEGORY_ICONS.get(result["category"], "📌")
    return result
```

**Step 2: Smoke test Claude enrichment**

Add temporary test in `__main__`:

```python
client = anthropic_sdk.Anthropic(api_key=ANTHROPIC_API_KEY)
test_video = {
    "title": "How to set up OpenClaw agents",
    "description": "In this video I show you how to configure multiple AI agents..."
}
result = enrich_video(client, test_video)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

Run: `python fetch.py`
Expected: valid JSON with category, summary, tags, prompts.

---

## Task 5: fetch.py — main orchestration + JSON output

**Files:**
- Modify: `fetch.py`

**Step 1: Add `load_existing` and `save_data` helpers**

```python
def load_existing() -> dict:
    """Load existing videos.json or return empty structure."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": "", "total": 0, "videos": []}


def save_data(data: dict) -> None:
    """Save data to videos.json."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

**Step 2: Replace `__main__` block with full orchestration**

```python
if __name__ == "__main__":
    from config import CHANNEL_ID

    print("🦞 OplacLaw Fetcher")
    print("=" * 40)

    # Build clients
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    ai_client = anthropic_sdk.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Load existing data
    existing = load_existing()
    existing_ids = {v["id"] for v in existing["videos"]}
    print(f"📦 Existing videos: {len(existing_ids)}")

    # Fetch all videos from channel
    print(f"🔍 Fetching videos from channel {CHANNEL_ID}...")
    raw_videos = fetch_all_videos(youtube, CHANNEL_ID)
    print(f"📺 Found {len(raw_videos)} total videos")

    # Filter to new ones only
    new_videos = [v for v in raw_videos if v["id"] not in existing_ids]
    print(f"✨ New videos to process: {len(new_videos)}")

    if not new_videos:
        print("✅ Nothing to update.")
    else:
        # Fetch durations for new videos
        new_ids = [v["id"] for v in new_videos]
        durations = fetch_video_durations(youtube, new_ids)

        # Enrich with Claude
        enriched = []
        for i, video in enumerate(new_videos, 1):
            print(f"  [{i}/{len(new_videos)}] Enriching: {video['title'][:60]}...")
            try:
                ai_data = enrich_video(ai_client, video)
                full_video = {
                    "id": video["id"],
                    "title": video["title"],
                    "title_highlight": ai_data.get("title_highlight", ""),
                    "url": video["url"],
                    "thumbnail": video["thumbnail"],
                    "published_at": video["published_at"],
                    "duration": durations.get(video["id"], ""),
                    "category": ai_data["category"],
                    "category_icon": ai_data["category_icon"],
                    "summary": ai_data.get("summary", ""),
                    "tags": ai_data.get("tags", []),
                    "prompts": ai_data.get("prompts", []),
                }
                enriched.append(full_video)
            except Exception as e:
                print(f"  ⚠️  Error processing {video['id']}: {e}")

        # Merge and save
        all_videos = enriched + existing["videos"]
        # Sort by published_at descending
        all_videos.sort(key=lambda v: v["published_at"], reverse=True)

        output = {
            "last_updated": datetime.utcnow().isoformat(),
            "total": len(all_videos),
            "videos": all_videos,
        }
        save_data(output)
        print(f"\n✅ Saved {len(all_videos)} videos to {DATA_FILE}")
        print(f"   ({len(enriched)} new, {len(existing_ids)} existing)")
```

**Step 3: Run the full fetch**

```bash
python fetch.py
```

Expected output:
```
🦞 OplacLaw Fetcher
========================================
📦 Existing videos: 0
🔍 Fetching videos from channel UC...
📺 Found N total videos
✨ New videos to process: N
  [1/N] Enriching: ...
  ...
✅ Saved N videos to data/videos.json
```

Verify `data/videos.json` exists and has valid content:
```bash
python -c "import json; d=json.load(open('data/videos.json')); print(d['total'], 'videos')"
```

**Step 4: Commit**

```bash
git add fetch.py config.py
git commit -m "feat: add YouTube + Claude data fetcher"
```

---

## Task 6: web/index.html

**Files:**
- Create: `web/index.html`

**Step 1: Create `web/index.html`**

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OplacLaw Use Cases</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

  <!-- NAVBAR -->
  <nav class="navbar">
    <div class="nav-left">
      <div class="logo">
        <span class="logo-icon">🦞</span>
        <div>
          <div class="logo-title">OplacLaw <span class="accent">Use Cases</span></div>
          <div class="logo-sub">由 oplaclaw 頻道整理</div>
        </div>
      </div>
    </div>
    <div class="nav-right">
      <span class="result-count" id="nav-count">— RESULTS</span>
      <a href="https://www.youtube.com/@oplaclaw" target="_blank" class="btn-outline">▶ YouTube</a>
    </div>
  </nav>

  <!-- HERO -->
  <section class="hero">
    <div class="hero-left">
      <div class="live-badge">● LIVE DATABASE</div>
      <h1 class="hero-title">
        <span class="accent" id="hero-count">—</span> 個<br>OpenClaw<br>使用案例
      </h1>
      <p class="hero-sub">從 oplaclaw 頻道收集的 OpenClaw 設定教學與應用案例。<br>提示詞可直接複製用於 Claude Code、Cursor 或任何 AI 工具。</p>
    </div>
    <div class="hero-right">
      <canvas id="donut-chart" width="200" height="200"></canvas>
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-num accent" id="stat-total">—</div>
          <div class="stat-label">Use Cases</div>
        </div>
        <div class="stat-card">
          <div class="stat-num accent" id="stat-cats">—</div>
          <div class="stat-label">Categories</div>
        </div>
      </div>
    </div>
  </section>

  <!-- FILTER BAR -->
  <section class="filter-bar">
    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input type="text" id="search-input" placeholder="搜尋使用案例..." />
    </div>
    <div class="filter-pills" id="filter-pills">
      <!-- injected by JS -->
    </div>
  </section>

  <!-- CARD GRID -->
  <main class="card-grid" id="card-grid">
    <div class="loading">載入中...</div>
  </main>

  <!-- NO RESULTS -->
  <div class="no-results" id="no-results" style="display:none">
    沒有符合的結果
  </div>

  <script src="app.js"></script>
</body>
</html>
```

**Step 2: Verify HTML opens in browser without errors**

Open `web/index.html` in browser. Should show navbar + hero skeleton + "載入中..." message.

---

## Task 7: web/style.css

**Files:**
- Create: `web/style.css`

**Step 1: Create `web/style.css`**

```css
/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0d0d0d;
  --card-bg: #1a1a1a;
  --border: #2a2a2a;
  --accent: #f97316;
  --accent-dark: #c2410c;
  --text: #f1f1f1;
  --muted: #888;
  --tag-bg: #252525;
  --radius: 12px;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  min-height: 100vh;
}

/* ── Navbar ── */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 100;
}

.nav-left { display: flex; align-items: center; }
.logo { display: flex; align-items: center; gap: 12px; }
.logo-icon { font-size: 28px; }
.logo-title { font-size: 16px; font-weight: 700; }
.logo-sub { font-size: 11px; color: var(--muted); }
.nav-right { display: flex; align-items: center; gap: 20px; }
.result-count { font-size: 13px; font-weight: 600; color: var(--muted); letter-spacing: 0.05em; }

.btn-outline {
  padding: 8px 16px;
  border: 1px solid var(--accent);
  border-radius: 8px;
  color: var(--accent);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.15s;
}
.btn-outline:hover { background: rgba(249,115,22,0.1); }

/* ── Hero ── */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60px 40px 40px;
  gap: 40px;
}

.hero-left { flex: 1; max-width: 520px; }
.live-badge { font-size: 12px; color: #4ade80; font-weight: 600; letter-spacing: 0.1em; margin-bottom: 20px; }
.hero-title { font-size: clamp(42px, 5vw, 64px); font-weight: 900; line-height: 1.1; margin-bottom: 20px; }
.hero-sub { font-size: 15px; color: var(--muted); line-height: 1.6; }

.accent { color: var(--accent); }

.hero-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

#donut-chart { width: 200px !important; height: 200px !important; }

.stat-cards { display: flex; flex-direction: column; gap: 12px; }
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 24px;
  min-width: 120px;
  text-align: center;
}
.stat-num { font-size: 36px; font-weight: 900; }
.stat-label { font-size: 12px; color: var(--muted); margin-top: 2px; }

/* ── Filter Bar ── */
.filter-bar {
  padding: 0 40px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 16px;
  max-width: 300px;
}
.search-wrap input {
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 14px;
  width: 100%;
}
.search-wrap input::placeholder { color: var(--muted); }

.filter-pills { display: flex; flex-wrap: wrap; gap: 8px; }

.pill {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.pill:hover { border-color: var(--accent); color: var(--accent); }
.pill.active { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }

/* ── Card Grid ── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  padding: 0 40px 60px;
}

/* ── Card ── */
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color 0.15s, transform 0.15s;
}
.card:hover { border-color: #444; transform: translateY(-2px); }

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-category {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
}
.cat-icon {
  width: 28px; height: 28px;
  background: #252525;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
}
.card-play-icon {
  color: var(--muted);
  cursor: pointer;
  font-size: 16px;
  text-decoration: none;
  transition: color 0.15s;
}
.card-play-icon:hover { color: var(--accent); }

.card-title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
}
.card-title .highlight { color: var(--accent); }

.card-summary {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
  padding: 4px 10px;
  background: var(--tag-bg);
  border-radius: 6px;
  font-size: 12px;
  color: var(--muted);
}

.card-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
}

.btn-copy {
  flex: 1;
  padding: 10px;
  background: #252525;
  border: none;
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background 0.15s;
}
.btn-copy:hover { background: #333; }
.btn-copy.copied { background: #166534; color: #4ade80; }

.btn-watch {
  padding: 10px 16px;
  background: var(--accent-dark);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s;
}
.btn-watch:hover { background: var(--accent); }

/* ── Loading / No results ── */
.loading { color: var(--muted); text-align: center; padding: 60px; grid-column: 1/-1; font-size: 16px; }
.no-results { color: var(--muted); text-align: center; padding: 60px; font-size: 16px; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .navbar { padding: 12px 20px; }
  .hero { flex-direction: column; padding: 30px 20px; }
  .hero-right { width: 100%; justify-content: center; }
  .filter-bar { padding: 0 20px 20px; }
  .card-grid { padding: 0 20px 40px; grid-template-columns: 1fr; }
}
```

---

## Task 8: web/app.js — data loading + card rendering

**Files:**
- Create: `web/app.js`

**Step 1: Create `web/app.js` — data loading + render**

```javascript
// ── State ──
let allVideos = [];
let activeCategory = 'All';
let searchQuery = '';

// ── Init ──
async function init() {
  try {
    const res = await fetch('../data/videos.json');
    if (!res.ok) throw new Error('Failed to load videos.json');
    const data = await res.json();
    allVideos = data.videos || [];
    renderStats(data);
    renderFilters();
    renderChart(data.videos);
    renderCards();
  } catch (e) {
    document.getElementById('card-grid').innerHTML =
      `<div class="loading">⚠️ 無法載入資料：${e.message}<br><small>請先執行 python fetch.py</small></div>`;
  }
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

// ── Search ──
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('search-input').addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase();
    renderCards();
  });
  init();
});

// ── Cards ──
function getFiltered() {
  return allVideos.filter(v => {
    const matchCat = activeCategory === 'All' || v.category === activeCategory;
    const matchSearch = !searchQuery ||
      v.title.toLowerCase().includes(searchQuery) ||
      v.summary.toLowerCase().includes(searchQuery) ||
      v.tags.some(t => t.toLowerCase().includes(searchQuery));
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
  const titleHtml = v.title_highlight
    ? v.title.replace(v.title_highlight, `<span class="highlight">${v.title_highlight}</span>`)
    : v.title;
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
```

---

## Task 9: web/app.js — donut chart

**Files:**
- Modify: `web/app.js`

**Step 1: Add `renderChart` function to `app.js`**

Add this function before `init()`:

```javascript
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
```

**Step 2: Open browser and verify**

Open `web/index.html`. You should see:
- Navbar with total count
- Hero with title, donut chart, stat boxes
- Filter pills for each category
- Cards in 3-column grid
- Search box filters cards in real time
- Copy Prompt copies to clipboard
- Watch button opens YouTube

**Step 3: Commit**

```bash
git add web/
git commit -m "feat: add frontend showcase page"
```

---

## Task 10: End-to-end verification

**Step 1: Run full fetch**

```bash
python fetch.py
```

Confirm `data/videos.json` has all videos with complete data.

**Step 2: Open and test frontend**

Open `web/index.html` in browser:
- [ ] Correct total count shown
- [ ] Donut chart renders with correct category colors
- [ ] Category filter pills work
- [ ] Search filters cards correctly
- [ ] Copy Prompt button copies text to clipboard
- [ ] Watch button opens YouTube in new tab

**Step 3: Final commit**

```bash
git add .
git commit -m "feat: complete oplaclaw showcase v1"
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `python fetch.py` | Fetch new videos + AI enrich → update JSON |
| Open `web/index.html` | View the showcase |
| Edit `data/videos.json` | Manual review / fix AI output |
| Edit `config.py` | Change categories or channel |
