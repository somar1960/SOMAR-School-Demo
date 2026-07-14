import os

# Student bot token
STUDENT_BOT_TOKEN = os.getenv("STUDENT_BOT_TOKEN")

# Admin bot token
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")

# Admin chat IDs (comma-separated in env, e.g., "123456,789012")
ADMIN_CHAT_IDS = [
    int(id.strip()) for id in os.getenv("ADMIN_CHAT_IDS", "").split(",") if id.strip()
]

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
