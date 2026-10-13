"""
HALALIA Core Logging & Observability
Production Version 1.1.0 — VERIFIED (Integration Complete)

التحسينات في v1.1.0:
    ✅ إصلاح استيراد get_logger
    ✅ إضافة metrics و timer للواجهة العامة
    ✅ إضافة PrometheusExporter
"""

from __future__ import annotations

# ==========================================================
# 1. Version
# ==========================================================
__version__ = "1.1.0"

# ==========================================================
# 2. Core Facade & Lifecycle
# ==========================================================
from .observability_service import observability_service

logger = observability_service


def initialize(config_service=None):
    """تهيئة نظام التسجيل والمراقبة"""
    return logger.initialize(config_service)


def shutdown():
    """إيقاف نظام التسجيل"""
    return logger.shutdown()


# ==========================================================
# 3. Context Management
# ==========================================================
request_context = logger.request_context

# ==========================================================
# 4. Logger Access (✅ مُصلَح)
# ==========================================================
from .logger_factory import get_logger, logger_factory

# ==========================================================
# 5. ✅ Metrics & Timer (جديد)
# ==========================================================
from ..monitoring.metrics import (
    metrics_service,
    metrics_registry,
    Counter,
    Gauge,
    Histogram,
    Summary,
    Timer,
    PrometheusExporter,
    ConsoleExporter,
)

# اختصارات مريحة
metrics = metrics_service
timer = metrics_service.timer


# ==========================================================
# 6. Monitoring & Health
# ==========================================================
def get_health_check():
    return logger.health_check()


def get_metrics():
    return logger.get_metrics()


# ==========================================================
# 7. Re-export Enums
# ==========================================================
from .logger_factory import LoggerName
from .log_filters import FilterType, MaskingStrategy
from .log_handlers import HandlerType
from .log_formatter import FormatterType
from ..monitoring.metrics import MetricType

# ==========================================================
# 8. Re-export Exceptions
# ==========================================================
from .logger_factory import UnknownLoggerError, LoggerRegistrationError
from .log_filters import UnknownFilterError, FilterRegistrationError
from .log_handlers import UnknownHandlerError, HandlerRegistrationError
from ..monitoring.metrics import MetricRegistrationError, MetricNotFoundError

# ==========================================================
# 9. Explicit Public API
# ==========================================================
__all__ = [
    # Metadata
    "__version__",

    # Lifecycle
    "initialize",
    "shutdown",

    # Main Facade
    "logger",
    "request_context",
    "get_logger",
    "logger_factory",

    # ✅ Metrics & Timer
    "metrics",
    "timer",
    "metrics_service",
    "metrics_registry",
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "Timer",
    "PrometheusExporter",
    "ConsoleExporter",

    # Monitoring
    "get_health_check",
    "get_metrics",

    # Enums
    "LoggerName",
    "FilterType",
    "MaskingStrategy",
    "HandlerType",
    "FormatterType",
    "MetricType",

    # Exceptions
    "UnknownLoggerError",
    "LoggerRegistrationError",
    "UnknownFilterError",
    "FilterRegistrationError",
    "UnknownHandlerError",
    "HandlerRegistrationError",
    "MetricRegistrationError",
    "MetricNotFoundError",
]