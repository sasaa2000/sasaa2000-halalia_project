"""
حلالية - نظام التشفير وفك التشفير
"""
import os
import logging
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)

class EncryptionManager:
    def __init__(self):
        self.key_file = Path(__file__).parent.parent / ".secret_key"
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # حماية الملف من القراءة بواسطة مستخدمين آخرين في النظام
            os.chmod(self.key_file, 0o600)
            logger.info("🔑 تم إنشاء مفتاح تشفير جديد وحمايته.")
            return key

    def encrypt(self, text: str) -> str:
        if not text: return ""
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text: return ""
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            logger.error(f"فشل فك التشفير: {e}")
            return encrypted_text

# نسخة عامة للاستخدام
encryptor = EncryptionManager()