"""
حلالية - نظام النسخ الاحتياطي التلقائي
"""
import logging
import subprocess
import os
from datetime import datetime
from pathlib import Path
import schedule
import time

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """نظام النسخ الاحتياطي لقاعدة البيانات"""
    
    def __init__(self, db_config: dict, backup_dir: str = None):
        self.db_config = db_config
        self.backup_dir = Path(backup_dir) if backup_dir else Path(__file__).parent.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # الاحتفاظ بآخر 7 نسخ فقط
        self.max_backups = 7
    
    def create_backup(self) -> str:
        """إنشاء نسخة احتياطية"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"halalia_backup_{timestamp}.sql"
            
            # أمر pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_config.get('host', 'localhost'),
                '-p', str(self.db_config.get('port', 5432)),
                '-U', self.db_config.get('user', 'postgres'),
                '-d', self.db_config.get('dbname', 'halalia_db'),
                '-f', str(backup_file)
            ]
            
            # تنفيذ الأمر
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config.get('password', '')
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_file}")
                
                # حذف النسخ القديمة
                self._cleanup_old_backups()
                
                return str(backup_file)
            else:
                logger.error(f"❌ فشل النسخ الاحتياطي: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"خطأ في النسخ الاحتياطي: {e}", exc_info=True)
            return None
    
    def _cleanup_old_backups(self):
        """حذف النسخ القديمة"""
        try:
            backups = sorted(self.backup_dir.glob("halalia_backup_*.sql"))
            
            if len(backups) > self.max_backups:
                for old_backup in backups[:-self.max_backups]:
                    old_backup.unlink()
                    logger.info(f"🗑️ تم حذف نسخة قديمة: {old_backup}")
                    
        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ: {e}")
    
    def restore_backup(self, backup_file: str):
        """استعادة نسخة احتياطية"""
        try:
            cmd = [
                'psql',
                '-h', self.db_config.get('host', 'localhost'),
                '-p', str(self.db_config.get('port', 5432)),
                '-U', self.db_config.get('user', 'postgres'),
                '-d', self.db_config.get('dbname', 'halalia_db'),
                '-f', backup_file
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config.get('password', '')
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ تم استعادة النسخة: {backup_file}")
                return True
            else:
                logger.error(f" فشل الاستعادة: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في الاستعادة: {e}", exc_info=True)
            return False
    
    def run_scheduler(self):
        """تشغيل جدولة النسخ الاحتياطي (يومياً الساعة 3 فجراً)"""
        schedule.every().day.at("03:00").do(self.create_backup)
        
        logger.info(" تم جدولة النسخ الاحتياطي اليومي (3:00 AM)")
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # فحص كل ساعة


# إنشاء instance عام
db_backup = None

def init_backup(db_config: dict):
    """تهيئة نظام النسخ الاحتياطي"""
    global db_backup
    db_backup = DatabaseBackup(db_config)
    
    # إنشاء نسخة احتياطية أولية
    db_backup.create_backup()
    
    # تشغيل الجدولة في خلفية منفصلة
    import threading
    scheduler_thread = threading.Thread(target=db_backup.run_scheduler, daemon=True)
    scheduler_thread.start()