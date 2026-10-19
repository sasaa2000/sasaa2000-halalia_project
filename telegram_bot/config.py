"""
حلالية - إعدادات البوت (محمية)
"""
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "Halalia_bot")

# Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME', 'halalia_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", 500))

# API URLs
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/analyze"
TIMEOUT = 10