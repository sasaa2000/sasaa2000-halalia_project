"""
© 2026 حَلَالِيّة - ملكية فكرية حصرية لـ أ. جمال الدين زيدان
محمية بموجب نظام حقوق المؤلف السعودي واتفاقية بيرن الدولية.
أي نسخ أو تعديل أو توزيع دون إذن كتابي مسبق يُعرض المخالف للمساءلة القانونية.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Any, Dict, List

class Database:
    _instance: Optional['Database'] = None
    
    def __new__(cls) -> 'Database':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = Path(__file__).parent.parent / 'halalia.db'
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
    
    def _connect(self):
        """الاتصال بقاعدة البيانات"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def get_connection(self) -> sqlite3.Connection:
        """الحصول على اتصال"""
        if self.conn is None:
            self._connect()
        return self.conn
    
    def close(self):
        """إغلاق الاتصال"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """تنفيذ استعلام"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
    
    def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """جلب جميع النتائج"""
        cursor = self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """جلب نتيجة واحدة"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

# نسخة عامة
db = Database()