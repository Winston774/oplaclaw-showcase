#!/usr/bin/env python3
"""Search YouTube for 'openclaw use cases' and enrich with Gemini AI."""

import json
import os
import re
from datetime import datetime

from google import genai
from googleapiclient.discovery import build

from config import (
    YOUTUBE_API_KEY,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    SEARCH_QUERIES,
    DATA_FILE,
    CATEGORIES,
    CATEGORY_ICONS,
)


def search_videos(youtube, query: str, max_results: int = 200) -> list[dict]:
    """Search YouTube videos by keyword. Returns up to max_results videos."""
    videos = []
    page_token = None

    while len(videos) < max_results:
        response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            order="relevance",
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

    return videos[:max_results]


def fetch_video_durations(youtube, video_ids: list[str]) -> dict[str, str]:
    """Fetch duration for a list of video IDs. Returns {id: 'MM:SS'}."""
    durations = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        response = youtube.videos().list(
            part="contentDetails",
            id=",".join(batch),
        ).execute()
        for item in response.get("items", []):
            raw = item["contentDetails"]["duration"]
            durations[item["id"]] = _parse_duration(raw)
    return durations


def _parse_duration(iso: str) -> str:
    """Convert PT8M5S → '8:05'."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return "0:00"
    hours, minutes, seconds = (int(x or 0) for x in m.groups())
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def enrich_video(client, video: dict) -> dict:
    """Send video title+description to Gemini, get category/summary/tags/prompts."""
    categories_str = ", ".join(CATEGORIES)
    prompt = f"""你是一個影片分析助手。根據以下 YouTube 影片資訊，以 JSON 格式回傳分析結果。

影片標題：{video['title']}

影片說明：{video['description'][:1000]}

## 分類規則（非常重要）

「OpenClaw Setup」只用於影片的**主要目的**是教人「安裝、設定、配置 OpenClaw/Clawdbot 工具本身」時。

如果影片展示了 OpenClaw 的**實際應用場景**，即使過程中有提到設定步驟，也應優先使用以下更具體的分類：
- 「內容行銷」→ 自動化內容創作、SEO、社群媒體、YouTube、部落格
- 「金融」→ 賺錢、交易、投資、加密貨幣、自動化收入
- 「生產力」→ 工作流程自動化、提升效率、任務自動化
- 「程式開發」→ 寫程式、建立應用、API 串接、工程師工作流
- 「自我成長」→ 個人助理、學習、習慣、自我提升
- 「生活管理」→ 生活日常自動化、行事曆、Email、待辦事項
- 「智慧居家」→ 智慧家電、Home Assistant、語音助理、IoT
- 「健康」→ 健康追蹤、運動、飲食、醫療
- 「E-Commerce」→ 電商、Shopify、dropshipping、Amazon

只有在影片**純粹是安裝教學、設定教學、安全設定、初始配置**，沒有明確應用場景時，才選「OpenClaw Setup」。

請回傳以下 JSON（不要加任何其他文字，不要用 markdown code block）：
{{
  "category": "從以下選一個: {categories_str}",
  "title_highlight": "標題中最重要的 2-4 個關鍵動作字詞（中文或英文）",
  "summary": "100字以內的繁體中文摘要，說明這部影片教什麼",
  "tags": ["關鍵字1", "關鍵字2", "關鍵字3"],
  "prompts": ["設定此功能所需的完整 AI 指令（若影片有提到的話，否則空陣列）"]
}}"""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    # Validate category
    if result.get("category") not in CATEGORIES:
        result["category"] = "其他"

    result["category_icon"] = CATEGORY_ICONS.get(result["category"], "📌")
    return result


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


if __name__ == "__main__":
    print("🦞 OplacLaw Fetcher")
    print("=" * 40)

    # Build clients
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

    # Load existing data
    existing = load_existing()
    existing_ids = {v["id"] for v in existing["videos"]}
    print(f"📦 Existing videos: {len(existing_ids)}")

    # Search YouTube across all queries, deduplicate
    seen_ids: set[str] = set(existing_ids)
    raw_videos: list[dict] = []
    for query, max_r in SEARCH_QUERIES:
        print(f"🔍 Searching: '{query}' (max {max_r})...")
        results = search_videos(youtube, query, max_results=max_r)
        new_in_query = [v for v in results if v["id"] not in seen_ids]
        seen_ids.update(v["id"] for v in new_in_query)
        raw_videos.extend(new_in_query)
        print(f"   +{len(new_in_query)} new (total so far: {len(raw_videos)})")

    print(f"📺 Total new videos to process: {len(raw_videos)}")

    # Filter to new ones only
    new_videos = raw_videos
    print(f"✨ New videos to process: {len(new_videos)}")

    if not new_videos:
        print("✅ Nothing to update.")
    else:
        # Fetch durations for new videos
        new_ids = [v["id"] for v in new_videos]
        durations = fetch_video_durations(youtube, new_ids)

        # Enrich with Gemini
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
        all_videos.sort(key=lambda v: v["published_at"], reverse=True)

        output = {
            "last_updated": datetime.utcnow().isoformat(),
            "total": len(all_videos),
            "videos": all_videos,
        }
        save_data(output)
        print(f"\n✅ Saved {len(all_videos)} videos to {DATA_FILE}")
        print(f"   ({len(enriched)} new, {len(existing_ids)} existing)")
