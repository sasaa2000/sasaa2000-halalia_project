"""
HALALIA Logging Configuration Defaults
Production Version 1.1.0 — VERIFIED (Final)

المؤسس:
    جمال الدين زيدان

التحسينات النهائية المطبقة:
    ✅ استخدام Protocol (ConfigReader) بدلاً من Any لتحسين Type Checking.
    ✅ إعادة تسمية dir إلى log_dir لتجنب تعارض الأسماء مع الدالة المدمجة.
    ✅ إضافة Validation للقيم (level, format, rotation).
    ✅ تضييق نطاق Exception إلى (AttributeError, ValueError, TypeError).
    ✅ قراءة إعدادات Rate Limit فعلياً من ConfigurationService.
    ✅ استخدام expanduser().resolve() لمسارات المجلدات.
    ✅ إضافة to_dict() و asdict لدعم التصدير.
    ✅ تقليل التكرار عبر مثيل DEFAULT_LOGGING_CONFIG واحد.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


# ==========================================================
# 1. Protocols (لضمان فك الارتباط وتحسين Type Checking)
# ==========================================================

class ConfigReader(Protocol):
    """واجهة مجردة لقراءة الإعدادات بأمان"""

    def get(self, key: str, default: str = ...) -> str: ...

    def get_bool(self, key: str, default: bool = ...) -> bool: ...

    def get_int(self, key: str, default: int = ...) -> int: ...


# ==========================================================
# 2. Constants & Validation Sets
# ==========================================================

CONFIG_VERSION = "1.1.0"

# قيم افتراضية آمنة
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "console"
DEFAULT_LOG_DIR = Path("runtime/logs")
DEFAULT_LOG_ROTATION = "size"
DEFAULT_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_LOG_BACKUP_COUNT = 5
DEFAULT_ENABLE_SENSITIVE_MASKING = True
DEFAULT_INCLUDE_PII_IN_MASKING = False
DEFAULT_ENABLE_RATE_LIMIT = False
DEFAULT_RATE_LIMIT_MAX_CALLS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60.0

# مجموعات التحقق من الصحة (Validation Sets)
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_FORMATS = {"console", "json", "detailed"}
VALID_ROTATIONS = {"none", "size", "time"}


# ==========================================================
# 3. Data Models
# ==========================================================

@dataclass(frozen=True)
class LoggingConfig:
    """
    تمثيل منظم وآمن لإعدادات التسجيل.
    frozen=True يضمن عدم التعديل بعد الإنشاء.
    """
    level: str
    log_format: str
    log_dir: Path
    rotation: str
    max_bytes: int
    backup_count: int
    enable_masking: bool
    include_pii: bool
    enable_rate_limit: bool
    rate_limit_max_calls: int
    rate_limit_window: float

    def to_dict(self) -> dict:
        """تحويل الإعدادات إلى قاموس (مفيد للـ Factories أو التصدير)"""
        return asdict(self)


# ==========================================================
# 4. Configuration Builder
# ==========================================================

# ✅ مثيل واحد ثابت للإعدادات الافتراضية (يقلل التكرار)
DEFAULT_LOGGING_CONFIG = LoggingConfig(
    level=DEFAULT_LOG_LEVEL,
    log_format=DEFAULT_LOG_FORMAT,
    log_dir=DEFAULT_LOG_DIR,
    rotation=DEFAULT_LOG_ROTATION,
    max_bytes=DEFAULT_LOG_MAX_BYTES,
    backup_count=DEFAULT_LOG_BACKUP_COUNT,
    enable_masking=DEFAULT_ENABLE_SENSITIVE_MASKING,
    include_pii=DEFAULT_INCLUDE_PII_IN_MASKING,
    enable_rate_limit=DEFAULT_ENABLE_RATE_LIMIT,
    rate_limit_max_calls=DEFAULT_RATE_LIMIT_MAX_CALLS,
    rate_limit_window=DEFAULT_RATE_LIMIT_WINDOW,
)


def get_default_config() -> LoggingConfig:
    """إرجاع الإعدادات الافتراضية الآمنة"""
    return DEFAULT_LOGGING_CONFIG


def build_logging_config(config_service: ConfigReader | None = None) -> LoggingConfig:
    """
    بناء إعدادات التسجيل النهائية بدمج القيم من ConfigurationService
    مع العودة للقيم الافتراضية الآمنة عند الفشل أو النقص.
    """
    if config_service is None:
        return DEFAULT_LOGGING_CONFIG

    try:
        # 1. قراءة القيم مع توفير الـ Fallback
        raw_level = str(config_service.get("APP_LOG_LEVEL", DEFAULT_LOG_LEVEL)).upper()
        raw_format = str(config_service.get("APP_LOG_FORMAT", DEFAULT_LOG_FORMAT)).lower()
        raw_dir = str(config_service.get("APP_LOG_DIR", str(DEFAULT_LOG_DIR.log_dir if hasattr(DEFAULT_LOG_DIR,
                                                                                               'log_dir') else DEFAULT_LOG_DIR)))
        raw_rotation = str(config_service.get("APP_LOG_ROTATION", DEFAULT_LOG_ROTATION)).lower()

        max_bytes = config_service.get_int("APP_LOG_MAX_SIZE", DEFAULT_LOG_MAX_BYTES)
        backup_count = config_service.get_int("APP_LOG_BACKUPS", DEFAULT_LOG_BACKUP_COUNT)

        enable_masking = config_service.get_bool("APP_LOG_SENSITIVE_MASKING", DEFAULT_ENABLE_SENSITIVE_MASKING)
        include_pii = config_service.get_bool("APP_LOG_INCLUDE_PII", DEFAULT_INCLUDE_PII_IN_MASKING)
        enable_rate_limit = config_service.get_bool("APP_LOG_RATE_LIMIT", DEFAULT_ENABLE_RATE_LIMIT)

        # ✅ قراءة إعدادات Rate Limit فعلياً
        rate_max_calls = config_service.get_int("APP_LOG_RATE_LIMIT_MAX_CALLS", DEFAULT_RATE_LIMIT_MAX_CALLS)
        rate_window = config_service.get_int("APP_LOG_RATE_LIMIT_WINDOW", DEFAULT_RATE_LIMIT_WINDOW)

        # 2. Validation (التحقق من الصحة)
        level = raw_level if raw_level in VALID_LEVELS else DEFAULT_LOG_LEVEL
        log_format = raw_format if raw_format in VALID_FORMATS else DEFAULT_LOG_FORMAT
        rotation = raw_rotation if raw_rotation in VALID_ROTATIONS else DEFAULT_LOG_ROTATION

        # 3. Path Resolution (توسيع المسار وحله بشكل مطلق)
        resolved_log_dir = Path(raw_dir).expanduser().resolve()

        return LoggingConfig(
            level=level,
            log_format=log_format,
            log_dir=resolved_log_dir,
            rotation=rotation,
            max_bytes=max_bytes,
            backup_count=backup_count,
            enable_masking=enable_masking,
            include_pii=include_pii,
            enable_rate_limit=enable_rate_limit,
            rate_limit_max_calls=rate_max_calls,
            rate_limit_window=float(rate_window),
        )

    # ✅ تضييق نطاق الاستثناءات لتجنب إخفاء الأخطاء البرمجية الحقيقية
    except (AttributeError, ValueError, TypeError) as e:
        # في بيئة الإنتاج، يمكن تسجيل هذا الخطأ هنا إذا كان الـ Logger متاحاً
        # logging.warning(f"Falling back to default logging config due to: {e}")
        return DEFAULT_LOGGING_CONFIG


# ==========================================================
# 5. Explicit Public API
# ==========================================================

__all__ = [
    "CONFIG_VERSION",
    "ConfigReader",
    "LoggingConfig",
    "DEFAULT_LOGGING_CONFIG",
    "get_default_config",
    "build_logging_config",
    "VALID_LEVELS",
    "VALID_FORMATS",
    "VALID_ROTATIONS",
]