# OplacLaw YouTube Showcase — Design Doc

**Date:** 2026-03-03
**Status:** Approved

---

## Overview

A static website that showcases YouTube content from the **oplaclaw** channel.
Data is collected via YouTube Data API v3, enriched by Claude AI (category, summary, prompts), stored as a JSON file, and rendered as a filterable card gallery.

---

## Goals

- Display all oplaclaw YouTube videos as browsable cards
- Show stats (total count, category donut chart) at the top
- Allow filtering by category and keyword search
- Each card shows: title, 100-char summary, category, tags, copy-prompt button, play button
- Data update workflow: run `python fetch.py` → review → refresh browser

---

## Architecture

```
Youtube_Claw/
├── fetch.py          # CLI: YouTube API → Claude API → writes data/videos.json
├── config.py         # API keys, channel ID, category list
├── requirements.txt  # Python dependencies
├── data/
│   └── videos.json   # All video data (source of truth)
└── web/
    ├── index.html    # Main page
    ├── style.css     # Styles (dark theme, orange accent)
    └── app.js        # Reads JSON, renders cards, chart, filters
```

**Execution flow:**
1. `python fetch.py` → calls YouTube Data API v3 → fetches all public videos from oplaclaw channel
2. For each video (title + description), sends to Claude API → returns: category, summary (繁中, ≤100 chars), tags, prompts list
3. Merges results → writes `data/videos.json`
4. User opens `web/index.html` in browser to view

---

## Data Schema

`data/videos.json`

```json
{
  "last_updated": "2026-03-03T10:00:00",
  "total": 42,
  "videos": [
    {
      "id": "youtube_video_id",
      "title": "影片標題",
      "title_highlight": "關鍵動作詞",
      "url": "https://www.youtube.com/watch?v=...",
      "thumbnail": "https://img.youtube.com/vi/.../hqdefault.jpg",
      "published_at": "2026-01-15",
      "duration": "8:05",
      "category": "OpenClaw Setup",
      "category_icon": "⚙️",
      "summary": "100字以內的繁體中文簡介",
      "tags": ["agent", "setup", "automation"],
      "prompts": [
        "設定 OpenClaw 所需的 AI 指令..."
      ]
    }
  ]
}
```

---

## Categories

| Name | Icon |
|------|------|
| OpenClaw Setup | ⚙️ |
| 內容行銷 | 📢 |
| 生產力 | ⚡ |
| 金融 | 💰 |
| 程式開發 | </> |
| 個人成長 | 🌱 |
| 生活管理 | 🏠 |
| 其他 | 📌 |

---

## Frontend Design

**Visual style:** Dark theme (`#0D0D0D` bg, `#1A1A1A` cards), orange accent (`#F97316`), white/gray text. Closely mirrors the OpenClaw Use Cases reference site.

**Page sections:**

1. **Navbar** — Logo, result count, GitHub link (optional)
2. **Hero** — Large title + subtitle, donut chart (Chart.js), stat boxes (total videos, total categories)
3. **Filter bar** — Search input + category filter pills (All active by default in orange)
4. **Card grid** — 3-column responsive grid

**Card layout:**
```
┌─────────────────────────────────────┐
│ [Category icon] Category name    [▶] │
│                                      │
│ **Highlighted** rest of title        │
│ Summary text truncated to 3 lines... │
│ [tag] [tag] [tag]                    │
│                                      │
│ [Copy Prompt]          [▶ 8:05]      │
└─────────────────────────────────────┘
```

- Title: first few words in orange, rest in white
- Copy Prompt: copies all prompts joined by newlines to clipboard
- Play button: opens YouTube URL in new tab
- Duration badge: orange pill in bottom right

---

## Python Script Design (`fetch.py`)

**Dependencies:** `google-api-python-client`, `anthropic`, `python-dotenv`

**Steps:**
1. Load existing `videos.json` (to skip already-processed videos)
2. Call YouTube Data API → list all videos from channel (paginated)
3. For each new video: call Claude API with title + description → parse JSON response
4. Merge old + new data → save `videos.json`
5. Print summary: X new, Y updated, Z total

**Claude prompt structure:**
- Input: video title + YouTube description
- Output (JSON): `{ category, summary, tags, prompts }`
- Category must be one of the predefined list

---

## Config (`config.py`)

```python
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CHANNEL_ID = "UCxxxxxx"  # oplaclaw channel ID

CATEGORIES = [
    "OpenClaw Setup", "內容行銷", "生產力",
    "金融", "程式開發", "個人成長", "生活管理", "其他"
]
```

Keys stored in `.env` file (gitignored).

---

## Out of Scope (This Version)

- Admin/review UI (manual edits done directly in videos.json)
- Backend server or database
- Automated scheduling (run fetch.py manually)
- Authentication or user accounts
