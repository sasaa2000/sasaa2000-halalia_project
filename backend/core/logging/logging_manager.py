"""
HALALIA Logging Manager
Production Version 2.0.0 — VERIFIED (Final)

المؤسس:
    جمال الدين زيدان

الوصف:
    المدير المركزي لمنطق تكوين نظام التسجيل.
    يحمل جميع التفاصيل التنفيذية (Handlers, Formatters, Filters).

    ObservabilityService → LoggingManager → Factories
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .logger_factory import LoggerFactory, logger_factory
from .log_formatter import FormatterFactory, FormatterType, formatter_factory
from .log_handlers import HandlerFactory, HandlerType, handler_factory
from .log_filters import (
    FilterFactory, FilterType, ContextFilter,
    filter_factory,
)

# ==========================================================
# 1. Constants & Enums
# ==========================================================

MANAGER_VERSION = "2.0.0"


class ManagerStatus(str):
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


# ==========================================================
# 2. Logging Manager
# ==========================================================

class LoggingManager:
    """
    المدير المركزي لمنطق تكوين التسجيل.
    Singleton Thread-Safe.
    """

    _instance: Optional["LoggingManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LoggingManager":
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
        self._status = ManagerStatus.NOT_INITIALIZED
        self._status_lock = threading.RLock()

        # Factories (مراجع)
        self._logger_factory = logger_factory
        self._formatter_factory = formatter_factory
        self._handler_factory = handler_factory
        self._filter_factory = filter_factory

        # Context Filter (احتفاظ مرجعي)
        self._context_filter: Optional[ContextFilter] = None

        # Handlers النشطة (للـ swap في Atomic Reload)
        self._active_handlers: List[logging.Handler] = []
        self._active_filters: List[logging.Filter] = []

        # Metrics
        self._setup_time_ms = 0.0
        self._reload_count = 0
        self._last_reload: Optional[str] = None
        self._startup_timestamp: Optional[str] = None
        self._last_exception: Optional[str] = None

    # ======================================================
    # Status Management
    # ======================================================

    @property
    def status(self) -> str:
        with self._status_lock:
            return self._status

    def _set_status(self, status: str) -> None:
        with self._status_lock:
            self._status = status

    @property
    def is_ready(self) -> bool:
        return self.status == ManagerStatus.READY

    # ======================================================
    # Public API - Configure
    # ======================================================

    def configure(
            self,
            environment: str,
            log_level: str = "INFO",
            log_format: str = "console",
            log_dir: str = "runtime/logs",
            log_json: bool = False,
            log_rotation: str = "none",
            log_max_size: int = 10485760,
            log_backups: int = 5,
            enable_masking: bool = True,
            enable_rate_limit: bool = False,
            include_pii: bool = False,
            app_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        self._set_status(ManagerStatus.INITIALIZING)
        start_time = time.perf_counter()

        try:
            formatter = self._initialize_formatter(
                log_format=log_format,
                log_json=log_json,
                is_production=(environment == "production"),
            )

            handlers = self._initialize_handlers(
                environment=environment,
                log_dir=log_dir,
                log_rotation=log_rotation,
                log_max_size=log_max_size,
                log_backups=log_backups,
                formatter=formatter,
            )

            filters = self._initialize_filters(
                environment=environment,
                app_version=app_version,
                enable_masking=enable_masking,
                enable_rate_limit=enable_rate_limit,
                include_pii=include_pii,
            )

            self._initialize_root_logger(
                log_level=log_level,
                handlers=handlers,
                filters=filters,
            )

            self._initialize_specialized_loggers(log_level=log_level)

            self._freeze_factories()

            end_time = time.perf_counter()
            self._setup_time_ms = (end_time - start_time) * 1000
            self._startup_timestamp = datetime.now(timezone.utc).isoformat()
            self._active_handlers = handlers
            self._active_filters = filters

            self._set_status(ManagerStatus.READY)
            self._last_exception = None

            return {
                "handlers_count": len(handlers),
                "filters_count": len(filters),
                "setup_time_ms": round(self._setup_time_ms, 2),
                "environment": environment,
                "log_level": log_level,
            }

        except Exception as e:
            self._set_status(ManagerStatus.FAILED)
            self._last_exception = f"{type(e).__name__}: {e}"
            raise

    # ======================================================
    # Private - Initialization Steps
    # ======================================================

    def _initialize_formatter(
            self,
            log_format: str,
            log_json: bool,
            is_production: bool,
    ) -> logging.Formatter:
        if log_json or log_format.lower() == "json":
            return self._formatter_factory.create(FormatterType.JSON)
        elif log_format.lower() == "detailed":
            return self._formatter_factory.create(FormatterType.DETAILED)
        else:
            return self._formatter_factory.create(
                FormatterType.CONSOLE,
                use_colors=not is_production,
            )

    def _initialize_handlers(
            self,
            environment: str,
            log_dir: str,
            log_rotation: str,
            log_max_size: int,
            log_backups: int,
            formatter: logging.Formatter,
    ) -> List[logging.Handler]:
        handlers: List[logging.Handler] = []

        if environment in ("development", "testing"):
            console_handler = self._handler_factory.create(HandlerType.CONSOLE)
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)

        if environment in ("production", "staging"):
            log_dir_path = Path(log_dir)

            if log_rotation == "size":
                file_handler = self._handler_factory.create(
                    HandlerType.ROTATING_FILE,
                    filename="halaliya.log",
                    log_dir=log_dir_path,
                    max_bytes=log_max_size,
                    backup_count=log_backups,
                )
            elif log_rotation == "time":
                file_handler = self._handler_factory.create(
                    HandlerType.TIMED_ROTATING,
                    filename="halaliya.log",
                    log_dir=log_dir_path,
                    when="midnight",
                    backup_count=log_backups,
                )
            else:
                file_handler = self._handler_factory.create(
                    HandlerType.FILE,
                    filename="halaliya.log",
                    log_dir=log_dir_path,
                )

            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        return handlers

    def _initialize_filters(
            self,
            environment: str,
            app_version: str,
            enable_masking: bool,
            enable_rate_limit: bool,
            include_pii: bool,
    ) -> List[logging.Filter]:
        filters: List[logging.Filter] = []

        self._context_filter = ContextFilter(
            environment=environment,
            application="HALALIA",
            version=app_version,
        )
        filters.append(self._context_filter)

        if enable_masking:
            sensitive_filter = self._filter_factory.create(
                FilterType.SENSITIVE_DATA,
                include_pii=include_pii,
            )
            filters.append(sensitive_filter)

        if enable_rate_limit:
            rate_limit_filter = self._filter_factory.create(
                FilterType.RATE_LIMIT,
                max_calls=100,
                window_seconds=60.0,
            )
            filters.append(rate_limit_filter)

        return filters

    def _initialize_root_logger(
            self,
            log_level: str,
            handlers: List[logging.Handler],
            filters: List[logging.Filter],
    ) -> None:
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        root_logger.handlers.clear()

        for handler in handlers:
            for fltr in filters:
                handler.addFilter(fltr)
            root_logger.addHandler(handler)

    def _initialize_specialized_loggers(self, log_level: str) -> None:
        level = getattr(logging, log_level.upper(), logging.INFO)
        self._logger_factory.initialize_specialized_loggers(
            level=level,
            propagate=False,
        )

    def _freeze_factories(self) -> None:
        self._formatter_factory.freeze()
        self._handler_factory.freeze()
        self._filter_factory.freeze()

    # ======================================================
    # Lifecycle - Shutdown
    # ======================================================

    def shutdown(self) -> Dict[str, Any]:
        if not self.is_ready:
            return {"closed_handlers": 0}

        closed_count = self._handler_factory.close_all()

        self._formatter_factory.clear_cache()
        self._handler_factory.clear_cache()
        self._filter_factory.clear_cache()

        self._active_handlers.clear()
        self._active_filters.clear()
        self._context_filter = None

        self._set_status(ManagerStatus.SHUTDOWN)

        return {"closed_handlers": closed_count}

    # ======================================================
    # Lifecycle - Atomic Reload
    # ======================================================

    def atomic_reload(self, **config_kwargs) -> Dict[str, Any]:
        if not self._context_filter:
            raise RuntimeError("Cannot reload before initial configuration")

        try:
            new_formatter = self._build_formatter_for_reload(**config_kwargs)
            new_handlers = self._build_handlers_for_reload(**config_kwargs)
            new_filters = self._build_filters_for_reload(**config_kwargs)

            for handler in new_handlers:
                for fltr in new_filters:
                    handler.addFilter(fltr)

            root_logger = logging.getLogger()
            old_handlers = list(root_logger.handlers)

            for handler in old_handlers:
                root_logger.removeHandler(handler)

            for handler in new_handlers:
                root_logger.addHandler(handler)

            for handler in old_handlers:
                try:
                    handler.close()
                except Exception:
                    pass

            self._active_handlers = new_handlers
            self._active_filters = new_filters
            self._reload_count += 1
            self._last_reload = datetime.now(timezone.utc).isoformat()

            return {
                "success": True,
                "swapped": True,
                "error": None,
                "reload_count": self._reload_count,
            }

        except Exception as e:
            return {
                "success": False,
                "swapped": False,
                "error": f"{type(e).__name__}: {e}",
                "reload_count": self._reload_count,
            }

    def _build_formatter_for_reload(self, **kwargs) -> logging.Formatter:
        log_format = kwargs.get("log_format", "console")
        log_json = kwargs.get("log_json", False)
        is_production = kwargs.get("environment", "development") == "production"
        return self._initialize_formatter(log_format, log_json, is_production)

    def _build_handlers_for_reload(self, **kwargs) -> List[logging.Handler]:
        return self._initialize_handlers(
            environment=kwargs.get("environment", "development"),
            log_dir=kwargs.get("log_dir", "runtime/logs"),
            log_rotation=kwargs.get("log_rotation", "none"),
            log_max_size=kwargs.get("log_max_size", 10485760),
            log_backups=kwargs.get("log_backups", 5),
            formatter=self._build_formatter_for_reload(**kwargs),
        )

    def _build_filters_for_reload(self, **kwargs) -> List[logging.Filter]:
        return self._initialize_filters(
            environment=kwargs.get("environment", "development"),
            app_version=kwargs.get("app_version", "1.0.0"),
            enable_masking=kwargs.get("enable_masking", True),
            enable_rate_limit=kwargs.get("enable_rate_limit", False),
            include_pii=kwargs.get("include_pii", False),
        )

    # ======================================================
    # Public API - Logger Access
    # ======================================================

    def get_logger(self, name: str) -> logging.Logger:
        return self._logger_factory.get_logger(name)

    @property
    def context_filter(self) -> Optional[ContextFilter]:
        return self._context_filter

    # ======================================================
    # Health & Metrics
    # ======================================================

    @property
    def uptime_seconds(self) -> float:
        if not self._startup_timestamp:
            return 0.0
        try:
            start = datetime.fromisoformat(self._startup_timestamp)
            now = datetime.now(timezone.utc)
            return (now - start).total_seconds()
        except Exception:
            return 0.0

    def health_check(self) -> Dict[str, Any]:
        if not self.is_ready:
            return {
                "healthy": False,
                "status": self.status,
                "reason": self._last_exception or "Not initialized",
            }

        score = self._calculate_health_score()

        return {
            "healthy": score >= 70,
            "health_score": score,
            "status": self.status,
            "setup_time_ms": round(self._setup_time_ms, 2),
            "uptime_seconds": round(self.uptime_seconds, 2),
            "reload_count": self._reload_count,
            "last_reload": self._last_reload,
            "last_exception": self._last_exception,
            "factories": {
                "formatter": self._formatter_factory.get_metrics(),
                "handler": self._handler_factory.get_metrics(),
                "filter": self._filter_factory.get_metrics(),
                "logger": self._logger_factory.get_metrics(),
            },
        }

    def _calculate_health_score(self) -> int:
        score = 100

        handler_metrics = self._handler_factory.get_metrics()
        if handler_metrics.get("closed_handlers_count", 0) > 10:
            score -= 10

        filter_metrics = self._filter_factory.get_metrics()
        if filter_metrics.get("cache_misses", 0) > filter_metrics.get("cache_hits", 0):
            score -= 15

        if self._last_exception:
            score -= 30

        return max(0, min(100, score))

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "version": MANAGER_VERSION,
            "status": self.status,
            "setup_time_ms": round(self._setup_time_ms, 2),
            "startup_timestamp": self._startup_timestamp,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "reload_count": self._reload_count,
            "last_reload": self._last_reload,
            "last_exception": self._last_exception,
            "active_handlers": len(self._active_handlers),
            "active_filters": len(self._active_filters),
            "factories": {
                "formatter": self._formatter_factory.get_metrics(),
                "handler": self._handler_factory.get_metrics(),
                "filter": self._filter_factory.get_metrics(),
                "logger": self._logger_factory.get_metrics(),
            },
        }

    # ======================================================
    # Metadata
    # ======================================================

    @property
    def version(self) -> str:
        return MANAGER_VERSION

    def __repr__(self) -> str:
        return (
            f"<LoggingManager "
            f"status={self.status} "
            f"uptime={round(self.uptime_seconds, 1)}s "
            f"reloads={self._reload_count}>"
        )


# ==========================================================
# 3. Global Instance
# ==========================================================
logging_manager = LoggingManager()

# ==========================================================
# 4. Explicit Public API
# ==========================================================
__all__ = [
    "MANAGER_VERSION",
    "ManagerStatus",
    "LoggingManager",
    "logging_manager",
]