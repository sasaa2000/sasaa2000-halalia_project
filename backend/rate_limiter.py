"""
حلالية - نظام الحد من الطلبات (Rate Limiting)
حماية من الهجمات والاستخدام المفرط
"""

import logging
import time
from collections import defaultdict
from threading import Lock
from backend.security_logger import log_suspicious_activity

logger = logging.getLogger(__name__)


class RateLimiter:
    """نظام الحد من الطلبات لكل مستخدم و IP"""

    def __init__(self):
        self.lock = Lock()

        # تخزين الطلبات
        self.requests_by_user = defaultdict(list)  # {user_id: [(timestamp, action)]}
        self.requests_by_ip = defaultdict(list)  # {ip: [(timestamp, action)]}

        # حدود الطلبات
        self.limits = {
            'analyze': {'max': 30, 'window': 3600, 'name': 'تحليل منتج'},
            'search': {'max': 60, 'window': 3600, 'name': 'بحث'},
            'save': {'max': 20, 'window': 3600, 'name': 'حفظ'},
            'review': {'max': 10, 'window': 3600, 'name': 'تقييم'},
            'alert': {'max': 15, 'window': 3600, 'name': 'تنبيه'},
            'wishlist': {'max': 25, 'window': 3600, 'name': 'قائمة رغبات'},
            'default': {'max': 100, 'window': 3600, 'name': 'طلب عام'},
        }

        # حدود IP (أكثر صرامة)
        self.ip_limits = {
            'analyze': {'max': 100, 'window': 3600},
            'default': {'max': 300, 'window': 3600},
        }

        self.banned_users = set()
        self.banned_ips = set()
        self.trusted_users = set()
        self.trusted_ips = set()

    def is_allowed(self, user_id: str, action: str = 'default', ip: str = None) -> dict:
        """التحقق من السماح بالطلب (User ID + IP)"""

        # 1. التحقق من المستخدم المحظور
        if user_id in self.banned_users:
            log_suspicious_activity(user_id, action, "مستخدم محظور")
            return {
                'allowed': False,
                'message': ' حسابك محظور. تواصل مع الدعم.',
                'retry_after': 0,
                'remaining': 0,
                'limit': 0
            }

        # 2. التحقق من IP المحظور
        if ip and ip in self.banned_ips:
            log_suspicious_activity(user_id, action, f"IP محظور: {ip}")
            return {
                'allowed': False,
                'message': '🚫 تم حظر الوصول من هذا العنوان.',
                'retry_after': 0,
                'remaining': 0,
                'limit': 0
            }

        # 3. المستخدمون الموثوقون
        if user_id in self.trusted_users or (ip and ip in self.trusted_ips):
            return {
                'allowed': True,
                'message': 'مسموح (موثوق)',
                'retry_after': 0,
                'remaining': 999,
                'limit': 999
            }

        with self.lock:
            now = time.time()
            limit_config = self.limits.get(action, self.limits['default'])
            max_requests = limit_config['max']
            window = limit_config['window']

            # 4. فحص حد User ID
            self.requests_by_user[user_id] = [
                (ts, act) for ts, act in self.requests_by_user[user_id]
                if now - ts < window
            ]

            user_requests = len(self.requests_by_user[user_id])

            if user_requests >= max_requests:
                oldest = min(ts for ts, _ in self.requests_by_user[user_id])
                retry_after = int(window - (now - oldest)) + 1

                log_suspicious_activity(user_id, action, f"تجاوز حد User ({max_requests})")
                logger.warning(f"⚠️ تجاوز الحد: user={user_id}, action={action}")

                return {
                    'allowed': False,
                    'message': (
                        f"️ تجاوزت الحد المسموح لـ '{limit_config['name']}'\n"
                        f"الحد: {max_requests} طلب/ساعة\n"
                        f"⏰ حاول مرة أخرى بعد {retry_after} ثانية"
                    ),
                    'retry_after': retry_after,
                    'remaining': 0,
                    'limit': max_requests
                }

            # 5. فحص حد IP (إذا متوفر)
            if ip:
                ip_limit_config = self.ip_limits.get(action, self.ip_limits['default'])
                ip_max = ip_limit_config['max']

                self.requests_by_ip[ip] = [
                    (ts, act) for ts, act in self.requests_by_ip[ip]
                    if now - ts < window
                ]

                ip_requests = len(self.requests_by_ip[ip])

                if ip_requests >= ip_max:
                    log_suspicious_activity(user_id, action, f"تجاوز حد IP ({ip_max})")
                    logger.warning(f"⚠️ تجاوز حد IP: ip={ip}, action={action}")

                    # حظر IP تلقائياً إذا تجاوز 3x الحد
                    if ip_requests >= ip_max * 3:
                        self.banned_ips.add(ip)
                        logger.critical(f"🚫 تم حظر IP تلقائياً: {ip}")

                    return {
                        'allowed': False,
                        'message': f"⚠️ تم حظر الوصول من هذا العنوان مؤقتاً.",
                        'retry_after': 3600,
                        'remaining': 0,
                        'limit': ip_max
                    }

                self.requests_by_ip[ip].append((now, action))

            # 6. تسجيل الطلب والسماح
            self.requests_by_user[user_id].append((now, action))

            return {
                'allowed': True,
                'message': 'مسموح',
                'retry_after': 0,
                'remaining': max_requests - user_requests - 1,
                'limit': max_requests
            }

    def get_usage_stats(self, user_id: str, action: str = 'default') -> dict:
        """الحصول على إحصائيات الاستخدام"""
        with self.lock:
            now = time.time()
            limit_config = self.limits.get(action, self.limits['default'])
            window = limit_config['window']

            recent = [
                (ts, act) for ts, act in self.requests_by_user[user_id]
                if now - ts < window
            ]

            total = len(recent)

            return {
                'used': total,
                'limit': limit_config['max'],
                'remaining': max(0, limit_config['max'] - total),
                'reset_in': int(window - (now - min(ts for ts, _ in recent))) if recent else 0,
                'percentage_used': (total / limit_config['max']) * 100
            }

    def ban_user(self, user_id: str, reason: str = ""):
        """حظر مستخدم"""
        self.banned_users.add(user_id)
        log_suspicious_activity(user_id, "ban", reason)
        logger.warning(f"🚫 تم حظر المستخدم: {user_id} - {reason}")

    def ban_ip(self, ip: str, reason: str = ""):
        """حظر IP"""
        self.banned_ips.add(ip)
        log_suspicious_activity("IP", "ban_ip", f"IP: {ip}, Reason: {reason}")
        logger.warning(f"🚫 تم حظر IP: {ip} - {reason}")

    def unban_user(self, user_id: str):
        """إلغاء حظر مستخدم"""
        self.banned_users.discard(user_id)
        logger.info(f"✅ تم إلغاء حظر المستخدم: {user_id}")

    def unban_ip(self, ip: str):
        """إلغاء حظر IP"""
        self.banned_ips.discard(ip)
        logger.info(f"✅ تم إلغاء حظر IP: {ip}")

    def add_trusted_user(self, user_id: str):
        """إضافة مستخدم موثوق"""
        self.trusted_users.add(user_id)
        logger.info(f"✅ تم إضافة مستخدم موثوق: {user_id}")

    def add_trusted_ip(self, ip: str):
        """إضافة IP موثوق"""
        self.trusted_ips.add(ip)
        logger.info(f"✅ تم إضافة IP موثوق: {ip}")

    def cleanup_old_requests(self):
        """تنظيف الطلبات القديمة"""
        with self.lock:
            now = time.time()
            for user_id in list(self.requests_by_user.keys()):
                self.requests_by_user[user_id] = [
                    (ts, act) for ts, act in self.requests_by_user[user_id]
                    if now - ts < 3600
                ]
                if not self.requests_by_user[user_id]:
                    del self.requests_by_user[user_id]

            for ip in list(self.requests_by_ip.keys()):
                self.requests_by_ip[ip] = [
                    (ts, act) for ts, act in self.requests_by_ip[ip]
                    if now - ts < 3600
                ]
                if not self.requests_by_ip[ip]:
                    del self.requests_by_ip[ip]

            logger.info("تم تنظيف الطلبات القديمة")

    def check_suspicious_behavior(self, user_id: str, ip: str = None) -> bool:
        """الكشف التلقائي عن السلوك المشبوه وحظره"""
        from backend.ip_analyzer import ip_analyzer
        from backend.audit_log import audit_logger

        # تتبع الطلب
        if ip:
            ip_analyzer.track_request(ip, user_id)

            # إذا كان IP مشبوه
            if ip_analyzer.is_suspicious(ip):
                location = ip_analyzer.get_location(ip)

                # حظر تلقائي
                self.ban_ip(ip,
                            f"سلوك مشبوه: {ip_analyzer.ip_tracking[ip]['requests']} طلب/ساعة من {location['country']}")
                audit_logger.log_failed_action(user_id, "auto_ban", f"IP: {ip}, Location: {location}")

                logger.critical(f"🚫 حظر تلقائي لـ IP: {ip} من {location['country']}")
                return True

        return False


# إنشاء instance عام
rate_limiter = RateLimiter()