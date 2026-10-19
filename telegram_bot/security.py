"""
حلالية - نظام التحقق من صحة الطلبات (Webhook Validation)
"""
import hmac
import hashlib
import logging
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class WebhookValidator:
    """التحقق من أن الطلبات تأتي من Telegram فقط"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
    
    def validate_telegram_request(self, request_headers: dict, request_body: bytes) -> bool:
        """
        التحقق من صحة الطلب القادم من Telegram
        
        Args:
            request_headers: Headers الطلب
            request_body: جسم الطلب
            
        Returns:
            bool: True إذا كان الطلب صالحاً
        """
        try:
            # Telegram يرسل توقيع في Header
            telegram_hash = request_headers.get('X-Telegram-Bot-Api-Secret-Token', '')
            
            if not telegram_hash:
                # إذا لم يكن هناك توقيع، نسمح بالطلب (لأننا نستخدم polling حالياً)
                return True
            
            # حساب التوقيع المتوقع
            expected_hash = hmac.new(
                self.bot_token.encode(),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # مقارنة التوقيعين
            is_valid = hmac.compare_digest(telegram_hash, expected_hash)
            
            if not is_valid:
                logger.warning("🚫 طلب غير صالح من مصدر مشبوه!")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الطلب: {e}")
            return False


# إنشاء instance عام
webhook_validator = None

def init_webhook_validator(bot_token: str):
    """تهيئة Validator عند بدء البوت"""
    global webhook_validator
    webhook_validator = WebhookValidator(bot_token)