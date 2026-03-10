#!/usr/bin/env python3
"""Generate deep summaries for all videos using YouTube transcripts + Gemini."""

import time
from datetime import datetime

from google import genai
from youtube_transcript_api import YouTubeTranscriptApi

from config import GEMINI_API_KEY, GEMINI_MODEL, DATA_FILE
from fetch import load_existing, save_data


def get_transcript(video_id: str) -> str | None:
    """Fetch YouTube transcript. Prefer English, fallback to any language."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            t = transcript_list.find_transcript(['en'])
        except Exception:
            try:
                t = transcript_list.find_generated_transcript(['en'])
            except Exception:
                t = next(iter(transcript_list))
        entries = t.fetch()
        text = ' '.join(e.get('text', '') for e in entries)
        return text[:6000]  # Limit tokens
    except Exception:
        return None


def generate_deep_summary(client, title: str, transcript: str) -> str:
    """Generate a 400-600 word Traditional Chinese deep summary via Gemini."""
    prompt = f"""你是一位影片分析師。以下是一部 YouTube 影片的字幕內容。
請生成一份 400-600 字的**繁體中文深度摘要**。

影片標題：{title}

字幕內容：
{transcript}

## 要求
- 長度：400-600 字
- 用 3-5 個段落，每段聚焦一個核心主題
- 涵蓋：影片教了什麼、關鍵步驟或概念、實際應用價值
- 具體實用，避免空洞的介紹語句
- 只回傳摘要內容，不需任何標題或前綴"""
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip()


if __name__ == "__main__":
    print("📚 Deep Summary Generator")
    print("=" * 50)

    ai_client = genai.Client(api_key=GEMINI_API_KEY)
    data = load_existing()
    videos = data["videos"]

    total = len(videos)
    already_done = sum(1 for v in videos if v.get('summary_long') is not None)
    to_process = total - already_done
    print(f"📦 Total: {total} | Already done: {already_done} | To process: {to_process}")
    print()

    processed = 0
    no_transcript = 0
    errors = 0

    for i, v in enumerate(videos, 1):
        # Skip if already processed (None = no transcript, string = has summary)
        if v.get('summary_long') is not None:
            continue

        title_short = v['title'][:60]
        print(f"  [{i:3d}/{total}] {title_short}...")

        transcript = get_transcript(v['id'])
        if not transcript:
            v['summary_long'] = ""  # Empty string = no transcript (won't retry)
            no_transcript += 1
            print(f"           ⚠️  No transcript")
            # Save periodically
            if (processed + no_transcript) % 10 == 0:
                save_data(data)
            continue

        try:
            v['summary_long'] = generate_deep_summary(ai_client, v['title'], transcript)
            processed += 1
            words = len(v['summary_long'])
            print(f"           ✅ {words} chars")
        except Exception as e:
            print(f"           ❌ Gemini error: {e}")
            errors += 1
            time.sleep(2)
            continue

        # Save every 10 videos
        if (processed + no_transcript) % 10 == 0:
            data["last_updated"] = datetime.utcnow().isoformat()
            save_data(data)
            print(f"  💾 Saved progress ({processed} done, {no_transcript} no-transcript)")

        time.sleep(0.3)  # Gentle rate limiting

    # Final save
    data["last_updated"] = datetime.utcnow().isoformat()
    save_data(data)

    print()
    print("=" * 50)
    print(f"✅ Generated: {processed}")
    print(f"⚠️  No transcript: {no_transcript}")
    print(f"❌ Errors: {errors}")
    print(f"💾 Saved to {DATA_FILE}")
