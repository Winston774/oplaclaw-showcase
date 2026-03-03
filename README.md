# OplacLaw YouTube Showcase

展示 oplaclaw YouTube 相關影片的靜態網站，使用 Gemini AI 分類與摘要。

## Setup

1. Copy `.env.example` to `.env` and fill in API keys
2. `pip install -r requirements.txt`
3. `python fetch.py` — fetches videos and generates `web/data/videos.json`
4. Open `web/index.html` in browser

## Getting API Keys

- YouTube Data API v3: https://console.cloud.google.com/
- Gemini API: https://aistudio.google.com/

## Data Update Workflow

```bash
python fetch.py       # fetch new videos
python reprocess.py   # re-classify existing videos (if prompt changes)
```

The data is saved to `web/data/videos.json` and committed to git for deployment.

## Deployment

Static site hosted on Zeabur. `zbpack.json` configures `web/` as the output directory.
