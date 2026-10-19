"""
حلالية - نظام CAPTCHA للطلبات المشبوهة
"""
import logging
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class CaptchaSystem:
    """نظام CAPTCHA للكشف عن البوتات"""
    
    def __init__(self):
        # {user_id: {'question': str, 'answer': str, 'expires': datetime}}
        self.pending_captchas = {}
        self.failed_attempts = defaultdict(int)  # {user_id: count}
        
        # حد الفشل قبل الحظر
        self.max_failures = 3
        
        # صلاحية CAPTCHA: 2 دقيقة
        self.captcha_expiry = timedelta(minutes=2)
    
    def generate_captcha(self, user_id: int) -> tuple:
        """توليد سؤال CAPTCHA بسيط"""
        # أسئلة حسابية بسيطة
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"كم نتيجة {num1} + {num2}؟"
        elif operation == '-':
            answer = num1 - num2
            question = f"كم نتيجة {num1} - {num2}؟"
        else:
            answer = num1 * num2
            question = f"كم نتيجة {num1} × {num2}؟"
        
        self.pending_captchas[user_id] = {
            'question': question,
            'answer': str(answer),
            'expires': datetime.now() + self.captcha_expiry
        }
        
        logger.info(f"تم توليد CAPTCHA للمستخدم {user_id}")
        return question, str(answer)
    
    def verify_captcha(self, user_id: int, answer: str) -> bool:
        """التحقق من إجابة CAPTCHA"""
        if user_id not in self.pending_captchas:
            return False
        
        captcha = self.pending_captchas[user_id]
        
        # التحقق من انتهاء الصلاحية
        if datetime.now() > captcha['expires']:
            del self.pending_captchas[user_id]
            return False
        
        # التحقق من الإجابة
        if captcha['answer'] == answer.strip():
            del self.pending_captchas[user_id]
            self.failed_attempts[user_id] = 0
            logger.info(f"تم حل CAPTCHA بنجاح للمستخدم {user_id}")
            return True
        
        # فشل
        self.failed_attempts[user_id] += 1
        logger.warning(f"فشل CAPTCHA للمستخدم {user_id} - المحاولات: {self.failed_attempts[user_id]}")
        
        # حظر بعد 3 محاولات فاشلة
        if self.failed_attempts[user_id] >= self.max_failures:
            logger.critical(f"تم حظر المستخدم {user_id} بعد {self.max_failures} محاولات فاشلة لـ CAPTCHA")
            return 'banned'
        
        return False
    
    def needs_captcha(self, user_id: str, action: str) -> bool:
        """تحديد إذا كان المستخدم يحتاج CAPTCHA"""
        # إذا فشل أكثر من مرتين في Rate Limiting
        from backend.rate_limiter import rate_limiter
        stats = rate_limiter.get_usage_stats(user_id, action)
        
        if stats['percentage_used'] > 80:
            return True
        
        return False
    
    def cleanup_expired(self):
        """تنظيف CAPTCHAs المنتهية"""
        now = datetime.now()
        expired = [
            uid for uid, data in self.pending_captchas.items()
            if now > data['expires']
        ]
        for uid in expired:
            del self.pending_captchas[uid]


# إنشاء instance عام
captcha_system = CaptchaSystem()