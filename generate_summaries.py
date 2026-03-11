#!/usr/bin/env python3
"""Generate deep summaries for all videos using YouTube transcripts + Gemini."""

import time
from datetime import datetime

from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, NoTranscriptFound, VideoUnavailable,
    IpBlocked, RequestBlocked,
)

from config import GEMINI_API_KEY, GEMINI_MODEL, DATA_FILE
from fetch import load_existing, save_data

# Sentinel stored in JSON to avoid retrying
NO_TRANSCRIPT = "NO_TRANSCRIPT"

_yt_api = YouTubeTranscriptApi()


def get_transcript(video_id: str):
    """Fetch YouTube transcript.
    Returns: text string, NO_TRANSCRIPT sentinel, or raises IpBlocked."""
    try:
        transcript_list = _yt_api.list(video_id)
        t = None
        for candidate in transcript_list:
            if candidate.language_code.startswith('en'):
                t = candidate
                break
        if t is None:
            tlist2 = _yt_api.list(video_id)
            t = next(iter(tlist2))
        fetched = t.fetch()
        text = ' '.join(s.text for s in fetched)
        return text[:6000]
    except (IpBlocked, RequestBlocked):
        raise  # Propagate so caller can pause and retry
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return NO_TRANSCRIPT
    except Exception:
        return NO_TRANSCRIPT


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

    generated = 0
    no_transcript = 0
    errors = 0
    ip_blocked_count = 0

    for i, v in enumerate(videos, 1):
        # Skip already processed (None key = not yet attempted)
        if v.get('summary_long') is not None:
            continue

        title_short = v['title'][:60]
        print(f"  [{i:3d}/{total}] {title_short}...")

        # Fetch transcript with IP-block handling
        transcript = None
        for attempt in range(3):
            try:
                transcript = get_transcript(v['id'])
                break
            except (IpBlocked, RequestBlocked):
                ip_blocked_count += 1
                wait = 30 * (attempt + 1)
                print(f"           🚫 IP blocked, waiting {wait}s...")
                time.sleep(wait)
        else:
            print(f"           ❌ Still blocked after 3 attempts, skipping batch")
            break

        if transcript == NO_TRANSCRIPT:
            v['summary_long'] = NO_TRANSCRIPT
            no_transcript += 1
            print(f"           ⚠️  No transcript")
        else:
            try:
                v['summary_long'] = generate_deep_summary(ai_client, v['title'], transcript)
                generated += 1
                print(f"           ✅ {len(v['summary_long'])} chars")
            except Exception as e:
                print(f"           ❌ Gemini error: {e}")
                errors += 1
                time.sleep(2)
                continue

        # Save every 10 videos
        if (generated + no_transcript) % 10 == 0:
            data["last_updated"] = datetime.utcnow().isoformat()
            save_data(data)
            print(f"  💾 Saved ({generated} summaries, {no_transcript} no-transcript)")

        time.sleep(2)  # 2s delay between requests to avoid IP block

    # Final save
    data["last_updated"] = datetime.utcnow().isoformat()
    save_data(data)

    print()
    print("=" * 50)
    print(f"✅ Generated: {generated}")
    print(f"⚠️  No transcript: {no_transcript}")
    print(f"❌ Errors: {errors}")
    print(f"🚫 IP blocks encountered: {ip_blocked_count}")
    print(f"💾 Saved to {DATA_FILE}")
