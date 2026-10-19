"""
حلالية - نظام التحقق من المدخلات (Input Validation)
"""
import re
import logging
from telegram_bot.config import MAX_INPUT_LENGTH

logger = logging.getLogger(__name__)


class InputValidator:
    """التحقق من صحة المدخلات"""
    
    @staticmethod
    def validate_text(text: str, max_length: int = None) -> tuple:
        """
        التحقق من نص المدخل
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        if max_length is None:
            max_length = MAX_INPUT_LENGTH
        
        # 1. فحص الطول
        if len(text) > max_length:
            return False, f"⚠️ النص طويل جداً. الحد الأقصى: {max_length} حرف."
        
        # 2. فحص المحتوى الضار
        dangerous_patterns = [
            r'<script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'import\s+os',
            r'import\s+sys',
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower):
                logger.warning(f" محتوى ضار مكتشف: {text[:50]}...")
                return False, "⚠️ محتوى غير مسموح به."
        
        # 3. فحص SQL Injection
        sql_patterns = [
            r'\b(drop|delete|update|insert|alter|truncate)\b.*\b(table|database)\b',
            r'\bunion\b.*\bselect\b',
            r'\bor\b\s+\d+=\d+',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text_lower):
                logger.warning(f" محاولة SQL Injection: {text[:50]}...")
                return False, "️ محتوى غير مسموح به."
        
        return True, ""
    
    @staticmethod
    def validate_product_name(name: str) -> tuple:
        """التحقق من اسم المنتج"""
        if not name or not name.strip():
            return False, "⚠️ اسم المنتج فارغ."
        
        if len(name) > 100:
            return False, "⚠️ اسم المنتج طويل جداً."
        
        # السماح بالأحرف العربية والإنجليزية والأرقام والمسافات فقط
        if not re.match(r'^[\u0600-\u06FFa-zA-Z0-9\s\-_.]+$', name):
            return False, "⚠️ اسم المنتج يحتوي على أحرف غير مسموحة."
        
        return True, ""
    
    @staticmethod
    def validate_command_args(args: list, max_args: int = 5) -> tuple:
        """التحقق من معاملات الأمر"""
        if len(args) > max_args:
            return False, f"⚠️ عدد المعاملات كبير جداً. الحد الأقصى: {max_args}."
        
        for arg in args:
            if len(arg) > 100:
                return False, "⚠️ أحد المعاملات طويل جداً."
        
        return True, ""


# إنشاء instance عام
input_validator = InputValidator()