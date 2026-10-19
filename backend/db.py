"""
حلالية - قاعدة البيانات مع حماية من SQL Injection
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import re

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_config):
        self.config = db_config
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.config)
            logger.info("✅ تم الاتصال بقاعدة البيانات")
        except Exception as e:
            logger.error(f"❌ فشل الاتصال: {e}")
            raise

    def execute_query(self, query, params=None, fetch=False):
        """تنفيذ استعلام مع حماية قصوى من SQL Injection"""
        try:
            # 1. فحص أمني سريع ضد الكلمات الخطرة جداً (طبقة دفاع إضافية)
            dangerous_keywords = ['DROP', 'TRUNCATE', 'ALTER TABLE', 'DELETE FROM products']
            if any(keyword in query.upper() for keyword in dangerous_keywords):
                logger.critical(f"🚫 محاولة هجوم SQL Injection مكتشفة: {query}")
                return None if not fetch else []

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # 2. التنفيذ الآمن باستخدام params (يمنع حقن SQL تماماً)
                cursor.execute(query, params or ())

                if fetch:
                    return cursor.fetchall()

                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ خطأ في قاعدة البيانات: {e}")
            self.connection.rollback()
            return None if not fetch else []

    def execute_one(self, query, params=None):
        """تنفيذ استعلام وإرجاع صف واحد"""
        results = self.execute_query(query, params, fetch=True)
        return results[0] if results else None

    def _is_safe_query(self, query: str) -> bool:
        """التحقق من أمان الاستعلام"""
        # منع الكلمات الخطرة
        dangerous_patterns = [
            r'\bDROP\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bUPDATE\b.*\bSET\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bALTER\b',
            r'\bTRUNCATE\b',
            r'--',
            r';',
            r'\bUNION\b',
            r'\bEXEC\b',
            r'\bEXECUTE\b',
        ]

        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                return False

        return True

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("تم إغلاق الاتصال بقاعدة البيانات")


# إنشاء instance عام
db = Database({
    'dbname': 'halalia_db',
    'user': 'postgres',
    'password': '2280',
    'host': 'localhost',
    'port': 5432
})
db.connect()