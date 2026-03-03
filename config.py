import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3-flash-preview"

# 搜尋查詢列表 — 每個查詢最多抓 50 支影片
SEARCH_QUERIES = [
    # 原有：OpenClaw 使用案例（廣泛）
    ("openclaw use cases", 200),
    # 內容行銷
    ("openclaw content marketing", 50),
    ("clawdbot content creation", 50),
    # 賺錢 / 金融
    ("openclaw make money", 50),
    ("clawdbot money", 50),
    # 生活管理
    ("openclaw life admin", 50),
    ("clawdbot life management", 50),
    # 自我成長
    ("openclaw personal growth", 50),
    ("clawdbot self improvement", 50),
    # 智慧居家
    ("openclaw smart home", 50),
    ("clawdbot home automation", 50),
    # 健康
    ("openclaw health", 50),
    ("clawdbot fitness", 50),
    # E-Commerce
    ("openclaw ecommerce", 50),
    ("clawdbot shopify", 50),
]

CATEGORIES = [
    "OpenClaw Setup",
    "內容行銷",
    "生產力",
    "金融",
    "程式開發",
    "自我成長",
    "生活管理",
    "智慧居家",
    "健康",
    "E-Commerce",
    "其他",
]

CATEGORY_ICONS = {
    "OpenClaw Setup": "⚙️",
    "內容行銷": "📢",
    "生產力": "⚡",
    "金融": "💰",
    "程式開發": "💻",
    "自我成長": "🌱",
    "生活管理": "🏠",
    "智慧居家": "🏡",
    "健康": "💪",
    "E-Commerce": "🛒",
    "其他": "📌",
}

DATA_FILE = "data/videos.json"
