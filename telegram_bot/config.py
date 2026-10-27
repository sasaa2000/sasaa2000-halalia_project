"""
© 2026 حَلَالِيّة - ملكية فكرية حصرية لـ أ. جمال الدين زيدان
محمية بموجب نظام حقوق المؤلف السعودي واتفاقية بيرن الدولية.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل .env من مجلد المشروع الرئيسي
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# ==========================================================
# Telegram Settings
# ==========================================================
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_IDS = os.getenv('ADMIN_IDS', '')
ADMIN_ID_LIST = [int(x.strip()) for x in ADMIN_IDS.split(',') if x.strip()] if ADMIN_IDS else []

# ==========================================================
# Environment
# ==========================================================
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# ==========================================================
# Base URL & API Settings
# ==========================================================
BASE_URL = os.getenv('BASE_URL', 'https://halaliya.com')
API_URL = os.getenv('API_URL', 'https://api.telegram.org')
API_VERSION = os.getenv('API_VERSION', 'v1')
TIMEOUT = int(os.getenv('TIMEOUT', '30'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '60'))

# ==========================================================
# Rate Limiting (الحماية من الهجمات)
# ==========================================================
MAX_INPUT_LENGTH = 1000
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VOICE_DURATION = 60  # seconds
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_CALLS = 100

# إعدادات Rate Limiting المتقدمة
RATE_LIMITS = {
    'default': {'calls': 30, 'period': 60},   # 30 طلب/دقيقة
    'analyze': {'calls': 10, 'period': 60},   # 10 تحليلات/دقيقة
    'search': {'calls': 20, 'period': 60},    # 20 بحث/دقيقة
    'admin': {'calls': 100, 'period': 60}     # 100 طلب/دقيقة للمدراء
}

# ==========================================================
# Database
# ==========================================================
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///halalia.db')
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

# ==========================================================
# AI Settings
# ==========================================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))

# ==========================================================
# Logging
# ==========================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.getenv('LOG_DIR', 'logs')

# ==========================================================
# Security (الحماية والتشفير)
# ==========================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'halalia-secret-key-2026')
SYSTEM_MASTER_PIN = os.getenv('SYSTEM_MASTER_PIN', '1234')

# مفتاح التشفير (لحماية البيانات الحساسة)
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')

# ==========================================================
# Features
# ==========================================================
ENABLE_VOICE = os.getenv('ENABLE_VOICE', 'true').lower() == 'true'
ENABLE_IMAGE_SEARCH = os.getenv('ENABLE_IMAGE_SEARCH', 'true').lower() == 'true'
MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'

# ==========================================================
# التحقق من التوكن
# ==========================================================
if not BOT_TOKEN:
    print("❌ BOT TOKEN NOT FOUND - Check .env file")
else:
    print("✅ Bot Token loaded successfully")
    print(f"👤 Admin IDs: {ADMIN_ID_LIST}")
    print(f"🌍 Environment: {ENVIRONMENT}")