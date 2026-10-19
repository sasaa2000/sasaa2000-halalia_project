"""
حلالية - نظام تسجيل العمليات (Audit Trail)
"""
import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    """تسجيل جميع العمليات الأمنية"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent / "logs" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ملف السجل الرئيسي
        self.log_file = self.log_dir / "audit.log"
    
    def log_action(self, user_id: str, action: str, details: dict = None, ip: str = None):
        """تسجيل عملية"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'action': action,
                'details': details or {},
                'ip': ip,
                'success': True
            }
            
            # كتابة في ملف JSON (أسهل للتحليل)
            json_log = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.json"
            
            with open(json_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # كتابة في ملف نصي (للقراءة السريعة)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry['timestamp']} | {user_id} | {action} | {details}\n")
            
            logger.info(f"Audit: {user_id} - {action}")
            
        except Exception as e:
            logger.error(f"خطأ في تسجيل Audit: {e}")
    
    def log_failed_action(self, user_id: str, action: str, reason: str, ip: str = None):
        """تسجيل عملية فاشلة"""
        self.log_action(user_id, action, {'reason': reason, 'success': False}, ip)
    
    def get_recent_logs(self, hours: int = 24) -> list:
        """الحصول على السجلات الأخيرة"""
        today = datetime.now().strftime('%Y%m%d')
        json_log = self.log_dir / f"audit_{today}.json"
        
        if not json_log.exists():
            return []
        
        logs = []
        with open(json_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        return logs[-100:]  # آخر 100 سجل


# إنشاء instance عام
audit_logger = AuditLogger()