"""
حلالية - إعدادات قاعدة البيانات PostgreSQL
"""

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "halalia_db",
    "user": "postgres",
    "password": "2280"  # ← غيّر هذا بكلمة مرورك
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"