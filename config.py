import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "@oplaclaw")

GEMINI_MODEL = "gemini-3-flash-preview"

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
