"""
حلالية - نظام المصادقة الثنائية للأوامر الحساسة
"""
import logging
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class TwoFactorAuth:
    """نظام 2FA للأوامر الإدارية الحساسة"""
    
    def __init__(self):
        # {user_id: {'code': str, 'expires': datetime}}
        self.pending_codes = {}
        self.verified_users = defaultdict(float)  # {user_id: timestamp}
        
        # صلاحية الكود: 5 دقائق
        self.code_expiry = timedelta(minutes=5)
        # صلاحية التحقق: 30 دقيقة
        self.verification_expiry = timedelta(minutes=30)
    
    def generate_code(self, user_id: int) -> str:
        """توليد كود 2FA"""
        code = ''.join(random.choices(string.digits, k=6))
        self.pending_codes[user_id] = {
            'code': code,
            'expires': datetime.now() + self.code_expiry
        }
        logger.info(f"تم توليد كود 2FA للمستخدم {user_id}")
        return code
    
    def verify_code(self, user_id: int, code: str) -> bool:
        """التحقق من كود 2FA"""
        if user_id not in self.pending_codes:
            return False
        
        pending = self.pending_codes[user_id]
        
        # التحقق من انتهاء الصلاحية
        if datetime.now() > pending['expires']:
            del self.pending_codes[user_id]
            return False
        
        # التحقق من الكود
        if pending['code'] == code:
            del self.pending_codes[user_id]
            self.verified_users[user_id] = datetime.now().timestamp()
            logger.info(f"تم التحقق من 2FA للمستخدم {user_id}")
            return True
        
        return False
    
    def is_verified(self, user_id: int) -> bool:
        """التحقق من أن المستخدم تم التحقق منه مؤخراً"""
        if user_id not in self.verified_users:
            return False
        
        last_verified = datetime.fromtimestamp(self.verified_users[user_id])
        if datetime.now() - last_verified > self.verification_expiry:
            del self.verified_users[user_id]
            return False
        
        return True
    
    def cleanup_expired(self):
        """تنظيف الأكواد المنتهية"""
        now = datetime.now()
        expired = [
            uid for uid, data in self.pending_codes.items()
            if now > data['expires']
        ]
        for uid in expired:
            del self.pending_codes[uid]


# إنشاء instance عام
two_factor_auth = TwoFactorAuth()