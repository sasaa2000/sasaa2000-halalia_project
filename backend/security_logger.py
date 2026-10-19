"""
حلالية - نظام مراقبة وتسجيل الأحداث الأمنية
"""
import logging
from pathlib import Path
import logging.handlers

# إنشاء مجلد السجلات إذا لم يكن موجوداً
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# إعداد مسجل خاص بالأمان
security_logger = logging.getLogger("halalia_security")
security_logger.setLevel(logging.WARNING) # نسجل التحذيرات والأخطاء فقط

# ملف يدور تلقائياً عند الوصول لـ 5 ميجابايت (يحتفظ بـ 3 نسخ احتياطية)
file_handler = logging.handlers.RotatingFileHandler(
    log_dir / "security.log",
    maxBytes=5*1024*1024,
    backupCount=3,
    encoding='utf-8'
)

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
file_handler.setFormatter(formatter)
security_logger.addHandler(file_handler)

def log_suspicious_activity(user_id: str, action: str, reason: str):
    """تسجيل نشاط مشبوه"""
    security_logger.warning(f"🚨 نشاط مشبوه | User: {user_id} | Action: {action} | Reason: {reason}")

def log_sql_injection_attempt(query: str):
    """تسجيل محاولة حقن SQL"""
    security_logger.critical(f"💀 محاولة SQL Injection | Query: {query}")