#!/usr/bin/env python3
"""Batch translate video titles to Traditional Chinese using Gemini."""

import json
import time
from datetime import datetime

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL, DATA_FILE
from fetch import load_existing, save_data


def translate_batch(client, videos: list[dict]) -> dict[str, str]:
    """Translate a batch of titles. Returns {id: title_zh}."""
    lines = "\n".join(f"{v['id']}|{v['title']}" for v in videos)
    prompt = f"""請將以下 YouTube 影片標題翻譯成自然的繁體中文。
每行格式為「ID|英文標題」，請回傳「ID|中文標題」，一行一個，不要加任何其他文字。

{lines}"""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    result = {}
    for line in response.text.strip().splitlines():
        if "|" in line:
            vid_id, _, title_zh = line.partition("|")
            result[vid_id.strip()] = title_zh.strip()
    return result


if __name__ == "__main__":
    print("🌐 Translating video titles to Traditional Chinese")
    print("=" * 50)

    client = genai.Client(api_key=GEMINI_API_KEY)
    data = load_existing()
    all_videos = data["videos"]

    # Only translate videos missing title_zh
    to_translate = [v for v in all_videos if not v.get("title_zh")]
    print(f"📦 Total videos: {len(all_videos)}")
    print(f"🔤 Need translation: {len(to_translate)}")

    if not to_translate:
        print("✅ All titles already translated.")
        exit(0)

    BATCH = 50
    translated = 0
    errors = 0

    for i in range(0, len(to_translate), BATCH):
        batch = to_translate[i:i + BATCH]
        print(f"  [{i + 1}–{min(i + BATCH, len(to_translate))}/{len(to_translate)}] translating...")
        try:
            results = translate_batch(client, batch)
            for video in batch:
                zh = results.get(video["id"])
                if zh:
                    video["title_zh"] = zh
                    translated += 1
                else:
                    errors += 1
        except Exception as e:
            print(f"  ⚠️  Batch error: {e}")
            errors += len(batch)
        time.sleep(0.5)  # gentle rate limit

    data["last_updated"] = datetime.utcnow().isoformat()
    save_data(data)

    print(f"\n✅ Done. {translated} translated, {errors} errors.")
    print(f"   Saved to {DATA_FILE}")
