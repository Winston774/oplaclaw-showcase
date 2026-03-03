#!/usr/bin/env python3
"""Re-enrich videos currently categorized as 'OpenClaw Setup' with the updated prompt."""

import json
import os
from datetime import datetime

from google import genai
from googleapiclient.discovery import build

from config import (
    YOUTUBE_API_KEY,
    GEMINI_API_KEY,
    DATA_FILE,
    CATEGORY_ICONS,
)
from fetch import enrich_video, load_existing, save_data

TARGET_CATEGORY = "OpenClaw Setup"


def fetch_snippets(youtube, video_ids: list[str]) -> dict[str, dict]:
    """Fetch title+description for a list of video IDs. Returns {id: {title, description}}."""
    snippets = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        response = youtube.videos().list(
            part="snippet",
            id=",".join(batch),
        ).execute()
        for item in response.get("items", []):
            s = item["snippet"]
            snippets[item["id"]] = {
                "id": item["id"],
                "title": s["title"],
                "description": s.get("description", ""),
            }
    return snippets


if __name__ == "__main__":
    print("🔄 Reprocessing 'OpenClaw Setup' videos with updated prompt")
    print("=" * 50)

    # Build clients
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

    # Load existing data
    data = load_existing()
    all_videos = data["videos"]

    # Find videos to reprocess
    to_reprocess = [v for v in all_videos if v.get("category") == TARGET_CATEGORY]
    print(f"📦 Total videos: {len(all_videos)}")
    print(f"🎯 '{TARGET_CATEGORY}' videos to reprocess: {len(to_reprocess)}")

    if not to_reprocess:
        print("✅ Nothing to reprocess.")
        exit(0)

    # Fetch full descriptions from YouTube
    ids = [v["id"] for v in to_reprocess]
    print(f"\n📡 Fetching descriptions from YouTube for {len(ids)} videos...")
    snippets = fetch_snippets(youtube, ids)
    print(f"   Got snippets for {len(snippets)} videos")

    # Re-enrich each video
    changed = 0
    errors = 0
    category_counts: dict[str, int] = {}

    for i, video in enumerate(to_reprocess, 1):
        vid_id = video["id"]
        snippet = snippets.get(vid_id)
        if not snippet:
            print(f"  [{i}/{len(to_reprocess)}] ⚠️  No snippet for {vid_id}, skipping")
            errors += 1
            continue

        print(f"  [{i}/{len(to_reprocess)}] {snippet['title'][:60]}...")
        try:
            ai_data = enrich_video(ai_client, snippet)
            new_category = ai_data["category"]
            category_counts[new_category] = category_counts.get(new_category, 0) + 1

            # Update in place
            video["category"] = new_category
            video["category_icon"] = CATEGORY_ICONS.get(new_category, "📌")
            video["title_highlight"] = ai_data.get("title_highlight", video.get("title_highlight", ""))
            video["summary"] = ai_data.get("summary", video.get("summary", ""))
            video["tags"] = ai_data.get("tags", video.get("tags", []))
            video["prompts"] = ai_data.get("prompts", video.get("prompts", []))

            if new_category != TARGET_CATEGORY:
                changed += 1
                print(f"         → {new_category}")
        except Exception as e:
            print(f"  ⚠️  Error on {vid_id}: {e}")
            errors += 1

    # Save updated data
    data["last_updated"] = datetime.utcnow().isoformat()
    save_data(data)

    print(f"\n✅ Done. Saved {len(all_videos)} videos to {DATA_FILE}")
    print(f"   {changed} reclassified away from '{TARGET_CATEGORY}'")
    print(f"   {errors} errors/skipped")
    print(f"\n📊 New category breakdown for reprocessed videos:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        icon = CATEGORY_ICONS.get(cat, "📌")
        print(f"   {icon} {cat}: {count}")
