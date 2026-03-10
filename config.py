import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3-flash-preview"

# 搜尋查詢列表 — 聚焦在真正的 use case 教學影片
SEARCH_QUERIES = [
    # 核心 use case 搜尋（精準）
    ("openclaw use case tutorial", 100),
    ("openclaw workflow automation", 100),
    ("openclaw tutorial how to", 100),
    ("openclaw automation setup guide", 50),
    # 領域別
    ("openclaw content marketing automation", 50),
    ("openclaw make money automate", 50),
    ("openclaw productivity workflow", 50),
    ("openclaw coding development", 50),
    ("openclaw ecommerce shopify", 50),
    ("openclaw smart home automation", 30),
    ("openclaw health fitness", 30),
    # Clawdbot（同生態系工具）
    ("clawdbot tutorial use case", 50),
    ("clawdbot automation", 50),
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

DATA_FILE = "web/data/videos.json"
