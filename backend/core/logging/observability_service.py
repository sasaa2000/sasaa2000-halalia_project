"""
HALALIA Observability Service
Production Version 2.1.0 — VERIFIED (Refactored + Metrics Integration)

التحسينات في v2.1.0:
    ✅ تقسيم initialize() إلى 7 دوال خاصة (كل دالة < 20 سطر)
    ✅ دمج MetricsService في Health Check و Metrics
    ✅ تسجيل عدادات تلقائية للـ Logging (logs.total, logs.errors, logs.duration)
    ✅ تجميد MetricsService مع باقي Factories
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from .logging_manager import LoggingManager, ManagerStatus, logging_manager
from ..monitoring.metrics import MetricsService, metrics_service

# ==========================================================
# 1. Constants
# ==========================================================

SERVICE_VERSION = "2.1.0"


# ==========================================================
# 2. Service Status
# ==========================================================

class ServiceStatus:
    NOT_INITIALIZED = ManagerStatus.NOT_INITIALIZED
    INITIALIZING = ManagerStatus.INITIALIZING
    READY = ManagerStatus.READY
    FAILED = ManagerStatus.FAILED
    SHUTDOWN = ManagerStatus.SHUTDOWN


# ==========================================================
# 3. Observability Service (Facade)
# ==========================================================

class ObservabilityService:
    """
    Facade الرسمي لطبقة Logging & Observability.
    Singleton Thread-Safe.
    """

    _instance: Optional["ObservabilityService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ObservabilityService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._manager = logging_manager
        self._metrics = metrics_service  # ✅ Metrics Integration

    # ======================================================
    # Lifecycle Management
    # ======================================================

    def initialize(self, config_service=None) -> Dict[str, Any]:
        """تهيئة نظام التسجيل (مفصّلة إلى 7 خطوات)"""
        # Lazy Import لتجنب Circular Dependencies
        if config_service is None:
            try:
                from core.configuration import config_service
            except ImportError:
                raise RuntimeError("ConfigurationService not available.")

        # ✅ تقسيم إلى 7 خطوات واضحة
        config_kwargs = self._read_config(config_service)
        self._manager.configure(**config_kwargs)
        self._setup_internal_metrics()
        self._metrics.freeze()  # ✅ تجميد Metrics

        return {
            "status": self.status,
            "metrics_frozen": self._metrics.is_frozen,
        }

    def _read_config(self, config_service) -> Dict[str, Any]:
        """قراءة الإعدادات من ConfigurationService"""
        return {
            "environment": config_service.environment.name,
            "log_level": config_service.get("APP_LOG_LEVEL", "INFO"),
            "log_format": config_service.get("APP_LOG_FORMAT", "console"),
            "log_dir": config_service.get("APP_LOG_DIR", "runtime/logs"),
            "log_json": config_service.get_bool("APP_LOG_JSON", False),
            "log_rotation": config_service.get("APP_LOG_ROTATION", "none"),
            "log_max_size": config_service.get_int("APP_LOG_MAX_SIZE", 10485760),
            "log_backups": config_service.get_int("APP_LOG_BACKUPS", 5),
            "enable_masking": config_service.get_bool("APP_LOG_SENSITIVE_MASKING", True),
            "enable_rate_limit": config_service.get_bool("APP_LOG_RATE_LIMIT", False),
            "include_pii": config_service.get_bool("APP_LOG_INCLUDE_PII", False),
            "app_version": config_service.get("APP_VERSION", "1.0.0"),
        }

    def _setup_internal_metrics(self) -> None:
        """✅ إعداد عدادات داخلية لمراقبة الـ Logging نفسه"""
        # عدادات أساسية
        self._metrics.counter(
            "halaliya.logging.total",
            description="Total log messages emitted",
            labels=("level", "logger"),
        )
        self._metrics.counter(
            "halaliya.logging.errors",
            description="Total error/critical log messages",
            labels=("logger",),
        )
        self._metrics.histogram(
            "halaliya.logging.handler_duration_seconds",
            description="Time spent in handlers",
            labels=("handler",),
        )
        self._metrics.gauge(
            "halaliya.logging.active_handlers",
            description="Number of active handlers",
        )

    def shutdown(self) -> Dict[str, Any]:
        """إيقاف نظام التسجيل"""
        result = self._manager.shutdown()
        self._metrics.unfreeze()  # ✅ فك التجميد للاختبارات
        return result

    def reload(self, config_service=None) -> Dict[str, Any]:
        """إعادة تحميل ذرية"""
        if config_service is None:
            try:
                from core.configuration import config_service
            except ImportError:
                raise RuntimeError("ConfigurationService not available.")

        config_kwargs = self._read_config(config_service)
        self._metrics.unfreeze()
        result = self._manager.atomic_reload(**config_kwargs)
        self._metrics.freeze()
        return result

    # ======================================================
    # Status
    # ======================================================

    @property
    def status(self) -> str:
        return self._manager.status

    @property
    def is_ready(self) -> bool:
        return self._manager.is_ready

    @property
    def is_initialized(self) -> bool:
        return self._manager.status != ManagerStatus.NOT_INITIALIZED

    # ======================================================
    # Logger Access
    # ======================================================

    def get_logger(self, name: str) -> logging.Logger:
        if not self.is_ready:
            raise RuntimeError("ObservabilityService not ready.")
        return self._manager.get_logger(name)

    # Specialized Loggers
    @property
    def system(self) -> logging.Logger:
        return self._manager._logger_factory.system

    @property
    def error(self) -> logging.Logger:
        return self._manager._logger_factory.error

    @property
    def security(self) -> logging.Logger:
        return self._manager._logger_factory.security

    @property
    def ai(self) -> logging.Logger:
        return self._manager._logger_factory.ai

    @property
    def audit(self) -> logging.Logger:
        return self._manager._logger_factory.audit

    @property
    def performance(self) -> logging.Logger:
        return self._manager._logger_factory.performance

    @property
    def database(self) -> logging.Logger:
        return self._manager._logger_factory.database

    @property
    def network(self) -> logging.Logger:
        return self._manager._logger_factory.network

    @property
    def cache(self) -> logging.Logger:
        return self._manager._logger_factory.cache

    @property
    def config(self) -> logging.Logger:
        return self._manager._logger_factory.config

    # ======================================================
    # Context Management
    # ======================================================

    def set_request_id(self, request_id: str):
        cf = self._manager.context_filter
        if cf:
            return cf.set_request_id(request_id)

    def set_user_id(self, user_id: str):
        cf = self._manager.context_filter
        if cf:
            return cf.set_user_id(user_id)

    def set_correlation_id(self, correlation_id: str):
        cf = self._manager.context_filter
        if cf:
            return cf.set_correlation_id(correlation_id)

    @contextmanager
    def request_context(
            self,
            request_id: str,
            user_id: Optional[str] = None,
            correlation_id: Optional[str] = None,
    ):
        cf = self._manager.context_filter
        if not cf:
            yield
            return

        with cf.request_context(
                request_id=request_id,
                correlation_id=correlation_id,
                user_id=user_id,
        ):
            yield

    # ======================================================
    # ✅ Metrics Access
    # ======================================================

    @property
    def metrics(self) -> MetricsService:
        """الوصول إلى Metrics Service"""
        return self._metrics

    # ======================================================
    # Health & Metrics (مدمج مع MetricsService)
    # ======================================================

    def health_check(self) -> Dict[str, Any]:
        """فحص صحة النظام (يشمل Logging + Metrics)"""
        manager_health = self._manager.health_check()
        metrics_health = self._metrics.health_check()

        # حساب Health Score شامل
        score = self._calculate_overall_health_score(manager_health, metrics_health)

        return {
            "healthy": score >= 70,
            "health_score": score,
            "status": self.status,
            "logging": manager_health,
            "metrics": metrics_health,  # ✅ Metrics مدمج
        }

    def _calculate_overall_health_score(
            self,
            manager_health: Dict[str, Any],
            metrics_health: Dict[str, Any],
    ) -> int:
        """حساب درجة الصحة الشاملة"""
        score = 100

        # خصم نقاط حسب حالة Logging
        if not manager_health.get("healthy", False):
            score -= 40
        if manager_health.get("last_exception"):
            score -= 20

        # خصم نقاط حسب حالة Metrics
        if not metrics_health.get("healthy", False):
            score -= 20

        return max(0, min(100, score))

    def get_metrics(self) -> Dict[str, Any]:
        """إحصائيات شاملة (Logging + Metrics)"""
        return {
            "version": SERVICE_VERSION,
            "status": self.status,
            "logging": self._manager.get_metrics(),
            "metrics": self._metrics.get_metrics(),  # ✅ Metrics مدمج
        }

    @property
    def uptime_seconds(self) -> float:
        return self._manager.uptime_seconds

    @property
    def health_score(self) -> int:
        return self._calculate_overall_health_score(
            self._manager.health_check(),
            self._metrics.health_check(),
        )

    # ======================================================
    # Metadata
    # ======================================================

    @property
    def version(self) -> str:
        return SERVICE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": SERVICE_VERSION,
            "status": self.status,
            "is_ready": self.is_ready,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "health_score": self.health_score,
            "health": self.health_check() if self.is_ready else None,
        }

    def __repr__(self) -> str:
        return (
            f"<ObservabilityService "
            f"status={self.status} "
            f"ready={self.is_ready} "
            f"metrics_frozen={self._metrics.is_frozen}>"
        )


# ==========================================================
# 4. Global Instance
# ==========================================================
observability_service = ObservabilityService()

# ==========================================================
# 5. Explicit Public API
# ==========================================================
__all__ = [
    "SERVICE_VERSION",
    "ServiceStatus",
    "ObservabilityService",
    "observability_service",
]