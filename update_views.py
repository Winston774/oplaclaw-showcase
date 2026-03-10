#!/usr/bin/env python3
"""Backfill view_count for all existing videos using YouTube API."""

from datetime import datetime
from googleapiclient.discovery import build

from config import YOUTUBE_API_KEY, DATA_FILE
from fetch import load_existing, save_data

if __name__ == "__main__":
    print("👁 Backfilling view counts")
    print("=" * 40)

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    data = load_existing()
    videos = data["videos"]
    ids = [v["id"] for v in videos]
    print(f"📦 Total videos: {len(ids)}")

    # Fetch statistics in batches of 50
    counts: dict[str, int] = {}
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        resp = youtube.videos().list(
            part="statistics",
            id=",".join(batch),
        ).execute()
        for item in resp.get("items", []):
            counts[item["id"]] = int(item["statistics"].get("viewCount", 0))
        print(f"  Fetched {min(i + 50, len(ids))}/{len(ids)}...")

    # Update view_count on each video
    for v in videos:
        v["view_count"] = counts.get(v["id"], 0)

    data["last_updated"] = datetime.utcnow().isoformat()
    save_data(data)
    print(f"\n✅ Done. Updated {len(videos)} videos.")
    print(f"   Saved to {DATA_FILE}")
