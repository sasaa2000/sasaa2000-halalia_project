"""
حلالية - نظام المراقبة والتنبيهات
"""
import logging
import requests
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class MonitoringSystem:
    """نظام مراقبة أداء البوت"""
    
    def __init__(self, bot_token: str, admin_chat_id: int = None):
        self.bot_token = bot_token
        self.admin_chat_id = admin_chat_id
        self.alerts_sent = defaultdict(int)  # {alert_type: count}
        self.last_alert_time = defaultdict(float)  # {alert_type: timestamp}
        
        # حدود التنبيهات (لمنع Spam)
        self.alert_limits = {
            'high_error_rate': 3600,  # تنبيه واحد كل ساعة
            'rate_limit_exceeded': 300,  # تنبيه واحد كل 5 دقائق
            'db_connection_failed': 600,  # تنبيه واحد كل 10 دقائق
        }
    
    def check_system_health(self) -> dict:
        """فحص صحة النظام"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': []
        }
        
        # 1. فحص قاعدة البيانات
        try:
            from backend.db import db
            result = db.execute_query("SELECT 1", fetch=True)
            if not result:
                health['status'] = 'critical'
                health['issues'].append('Database connection failed')
        except Exception as e:
            health['status'] = 'critical'
            health['issues'].append(f'Database error: {str(e)}')
        
        # 2. فحص Rate Limiter
        try:
            from backend.rate_limiter import rate_limiter
            stats = rate_limiter.get_usage_stats('monitoring', 'default')
            if stats['percentage_used'] > 90:
                health['status'] = 'warning'
                health['issues'].append('Rate limit near capacity')
        except Exception as e:
            health['issues'].append(f'Rate limiter error: {str(e)}')
        
        return health
    
    async def send_alert(self, alert_type: str, message: str):
        """إرسال تنبيه للأدمن"""
        try:
            # التحقق من حدود التنبيهات
            now = datetime.now().timestamp()
            limit = self.alert_limits.get(alert_type, 3600)
            
            if now - self.last_alert_time[alert_type] < limit:
                return  # لا ترسل تنبيه متكرر
            
            if not self.admin_chat_id:
                logger.warning(f"تنبيه بدون Admin Chat ID: {message}")
                return
            
            # إرسال التنبيه عبر Telegram
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.admin_chat_id,
                'text': f"🚨 <b>تنبيه أمني:</b>\n\n{message}",
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.last_alert_time[alert_type] = now
                self.alerts_sent[alert_type] += 1
                logger.info(f"تم إرسال تنبيه: {alert_type}")
            else:
                logger.error(f"فشل إرسال التنبيه: {response.status_code}")
                
        except Exception as e:
            logger.error(f"خطأ في إرسال التنبيه: {e}")
    
    def get_alerts_summary(self) -> dict:
        """ملخص التنبيهات"""
        return {
            'total_alerts': sum(self.alerts_sent.values()),
            'alerts_by_type': dict(self.alerts_sent),
            'last_alert_times': {
                k: datetime.fromtimestamp(v).strftime('%Y-%m-%d %H:%M:%S')
                for k, v in self.last_alert_time.items()
            }
        }


# إنشاء instance عام
monitoring_system = None

def init_monitoring(bot_token: str, admin_chat_id: int = None):
    """تهيئة نظام المراقبة"""
    global monitoring_system
    monitoring_system = MonitoringSystem(bot_token, admin_chat_id)
    logger.info("🔍 تم تهيئة نظام المراقبة")