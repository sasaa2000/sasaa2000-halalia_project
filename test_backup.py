"""
اختبار النسخ الاحتياطي
"""
from backend.backup import DatabaseBackup
from telegram_bot.config import DB_CONFIG

# إنشاء نسخة احتياطية
backup = DatabaseBackup(DB_CONFIG)
result = backup.create_backup()

if result:
    print(f"✅ تم إنشاء نسخة احتياطية: {result}")
else:
    print("❌ فشل النسخ الاحتياطي")