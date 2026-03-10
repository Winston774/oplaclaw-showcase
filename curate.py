#!/usr/bin/env python3
"""Re-classify all existing videos using Gemini to filter out non-use-case content."""

import json
import time
from datetime import datetime

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL, DATA_FILE
from fetch import load_existing, save_data


PROMPT_TEMPLATE = """你是影片相關性判斷員。判斷此 YouTube 影片是否為 OpenClaw/Clawdbot 的真正 use case 或教學。

標題：{title}
摘要：{summary}

回傳 JSON（不含其他文字，不用 markdown code block）：
{{"is_use_case": true 或 false, "reason": "一句話說明"}}

判斷規則：
- true: 實際操作 demo、step-by-step 教學、工作流程展示、安裝/設定指南
- false（符合任一項即 false）:
  * 比較影片（vs、versus、destroys、alternatives、which is better）
  * 訪談/Podcast 節目（如 Lex Fridman、podcast、interview、Q&A、standup）
  * 爭議/戲劇性內容（scam、ban、malware、controversy、exposed）
  * 建立「像 OpenClaw 的替代品」（影片主角是其他 AI 工具，OpenClaw 是被比較對象）
  * 通用 AI 討論，OpenClaw 只是簡短提及或標題噱頭
  * 純評論/意見/吐槽，不含實際操作步驟"""


def classify_video(client, v: dict) -> dict:
    summary_text = v.get("summary", "") or v.get("description", "")[:200]
    prompt = PROMPT_TEMPLATE.format(
        title=v["title"],
        summary=summary_text[:300],
    )
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    raw = response.text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


if __name__ == "__main__":
    print("✂️  OpenClaw Video Curator")
    print("=" * 50)

    ai_client = genai.Client(api_key=GEMINI_API_KEY)
    data = load_existing()
    videos = data["videos"]
    total = len(videos)
    print(f"📦 Total videos to classify: {total}")
    print()

    kept = []
    removed = []
    errors = []

    for i, v in enumerate(videos, 1):
        title_short = v["title"][:65]
        try:
            result = classify_video(ai_client, v)
            is_use_case = result.get("is_use_case", True)
            reason = result.get("reason", "")

            if is_use_case:
                kept.append(v)
                status = "✅"
            else:
                removed.append({"title": v["title"], "reason": reason})
                status = "❌"

            print(f"  [{i:3d}/{total}] {status} {title_short}")
            if not is_use_case:
                print(f"          → {reason}")

        except Exception as e:
            print(f"  [{i:3d}/{total}] ⚠️  Error: {e} — keeping video")
            kept.append(v)
            errors.append(v["title"])

        # Small delay to avoid rate limiting
        if i % 20 == 0:
            time.sleep(1)

    print()
    print("=" * 50)
    print(f"✅ Kept:    {len(kept)}")
    print(f"❌ Removed: {len(removed)}")
    if errors:
        print(f"⚠️  Errors:  {len(errors)} (kept by default)")

    print()
    print("📋 Removed videos:")
    for r in removed:
        print(f"  - {r['title'][:70]}")
        print(f"    Reason: {r['reason']}")

    # Save filtered data
    output = {
        "last_updated": datetime.utcnow().isoformat(),
        "total": len(kept),
        "videos": kept,
    }
    save_data(output)
    print()
    print(f"💾 Saved {len(kept)} videos to {DATA_FILE}")
