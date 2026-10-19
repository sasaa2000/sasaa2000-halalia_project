"""
حلالية - تحليل IP للكشف عن الهجمات
"""
import logging
import requests
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IPAnalyzer:
    """تحليل عناوين IP للكشف عن السلوك المشبوه"""
    
    def __init__(self):
        # {ip: {'requests': int, 'first_seen': datetime, 'last_seen': datetime}}
        self.ip_tracking = defaultdict(lambda: {
            'requests': 0,
            'first_seen': datetime.now(),
            'last_seen': datetime.now(),
            'countries': set()
        })
        
        # حد الطلبات قبل الشك
        self.suspicious_threshold = 50  # طلب/ساعة
        
        # Cache للـ Geolocation
        self.geo_cache = {}
    
    def track_request(self, ip: str, user_id: str = None):
        """تتبع طلب من IP"""
        tracking = self.ip_tracking[ip]
        tracking['requests'] += 1
        tracking['last_seen'] = datetime.now()
        
        # تنظيف البيانات القديمة (أكثر من ساعة)
        if datetime.now() - tracking['first_seen'] > timedelta(hours=1):
            tracking['requests'] = 1
            tracking['first_seen'] = datetime.now()
    
    def is_suspicious(self, ip: str) -> bool:
        """التحقق إذا كان IP مشبوه"""
        if ip not in self.ip_tracking:
            return False
        
        tracking = self.ip_tracking[ip]
        
        # إذا تجاوز الحد
        if tracking['requests'] > self.suspicious_threshold:
            logger.warning(f"IP مشبوه: {ip} - {tracking['requests']} طلب/ساعة")
            return True
        
        return False
    
    def get_location(self, ip: str) -> dict:
        """الحصول على موقع IP (مع Cache)"""
        if ip in self.geo_cache:
            return self.geo_cache[ip]
        
        try:
            # استخدام API مجاني
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = response.json()
            
            if data['status'] == 'success':
                location = {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown')
                }
                self.geo_cache[ip] = location
                return location
            
        except Exception as e:
            logger.error(f"خطأ في Geolocation: {e}")
        
        return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}
    
    def get_suspicious_ips(self) -> list:
        """الحصول على قائمة IPs المشبوهة"""
        suspicious = []
        for ip, tracking in self.ip_tracking.items():
            if tracking['requests'] > self.suspicious_threshold:
                location = self.get_location(ip)
                suspicious.append({
                    'ip': ip,
                    'requests': tracking['requests'],
                    'location': location,
                    'last_seen': tracking['last_seen'].isoformat()
                })
        
        return sorted(suspicious, key=lambda x: x['requests'], reverse=True)
    
    def cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        now = datetime.now()
        expired = [
            ip for ip, tracking in self.ip_tracking.items()
            if now - tracking['last_seen'] > timedelta(hours=2)
        ]
        for ip in expired:
            del self.ip_tracking[ip]


# إنشاء instance عام
ip_analyzer = IPAnalyzer()