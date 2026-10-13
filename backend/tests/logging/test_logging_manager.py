"""
اختبارات الوحدة لـ logging_manager.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.logging.log_formatter import FormatterType
from core.logging.log_handlers import HandlerType
from core.logging.logging_manager import (
    MANAGER_VERSION,
    LoggingManager,
    ManagerStatus,
)


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def manager():
    LoggingManager._instance = None
    root = logging.getLogger()
    saved_handlers = list(root.handlers)

    m = LoggingManager()
    # Mocks لتجنب إنشاء handlers حقيقية أو تجميد Factories
    m._logger_factory = MagicMock()
    m._formatter_factory = MagicMock()
    m._handler_factory = MagicMock()
    m._filter_factory = MagicMock()

    yield m

    # تنظيف root logger
    root.handlers.clear()
    for h in saved_handlers:
        root.addHandler(h)
    LoggingManager._instance = None


# ==========================================================
# 1. Status
# ==========================================================

class TestStatus:
    def test_initial_status(self, manager):
        assert manager.status == ManagerStatus.NOT_INITIALIZED
        assert manager.is_ready is False

    def test_set_status(self, manager):
        manager._set_status(ManagerStatus.READY)
        assert manager.status == ManagerStatus.READY
        assert manager.is_ready is True


# ==========================================================
# 2. _initialize_formatter
# ==========================================================

class TestInitializeFormatter:
    def test_json_formatter(self, manager):
        manager._initialize_formatter("console", log_json=True, is_production=False)
        manager._formatter_factory.create.assert_called_with(FormatterType.JSON)

    def test_json_by_format_name(self, manager):
        manager._initialize_formatter("json", log_json=False, is_production=False)
        manager._formatter_factory.create.assert_called_with(FormatterType.JSON)

    def test_detailed_formatter(self, manager):
        manager._initialize_formatter("detailed", log_json=False, is_production=False)
        manager._formatter_factory.create.assert_called_with(FormatterType.DETAILED)

    def test_console_formatter_dev(self, manager):
        manager._initialize_formatter("console", log_json=False, is_production=False)
        manager._formatter_factory.create.assert_called_with(
            FormatterType.CONSOLE, use_colors=True
        )

    def test_console_formatter_production(self, manager):
        manager._initialize_formatter("console", log_json=False, is_production=True)
        manager._formatter_factory.create.assert_called_with(
            FormatterType.CONSOLE, use_colors=False
        )


# ==========================================================
# 3. _initialize_handlers
# ==========================================================

class TestInitializeHandlers:
    def test_development_console(self, manager):
        handlers = manager._initialize_handlers(
            "development", "logs", "none", 100, 5, MagicMock()
        )
        assert len(handlers) == 1
        manager._handler_factory.create.assert_called_with(HandlerType.CONSOLE)

    def test_production_file_no_rotation(self, manager):
        handlers = manager._initialize_handlers(
            "production", "logs", "none", 100, 5, MagicMock()
        )
        assert len(handlers) == 1
        manager._handler_factory.create.assert_called_with(
            HandlerType.FILE, filename="halaliya.log", log_dir=Path("logs")
        )

    def test_production_size_rotation(self, manager):
        manager._initialize_handlers(
            "production", "logs", "size", 1000, 3, MagicMock()
        )
        manager._handler_factory.create.assert_called_with(
            HandlerType.ROTATING_FILE,
            filename="halaliya.log",
            log_dir=Path("logs"),
            max_bytes=1000,
            backup_count=3,
        )

    def test_production_time_rotation(self, manager):
        manager._initialize_handlers(
            "production", "logs", "time", 1000, 3, MagicMock()
        )
        manager._handler_factory.create.assert_called_with(
            HandlerType.TIMED_ROTATING,
            filename="halaliya.log",
            log_dir=Path("logs"),
            when="midnight",
            backup_count=3,
        )

    def test_staging_file(self, manager):
        handlers = manager._initialize_handlers(
            "staging", "logs", "none", 100, 5, MagicMock()
        )
        assert len(handlers) == 1


# ==========================================================
# 4. _initialize_filters
# ==========================================================

class TestInitializeFilters:
    def test_all_filters_enabled(self, manager):
        filters = manager._initialize_filters("dev", "1.0", True, True, False)
        assert len(filters) == 3  # context + sensitive + rate_limit

    def test_only_context_filter(self, manager):
        filters = manager._initialize_filters("dev", "1.0", False, False, False)
        assert len(filters) == 1

    def test_context_filter_stored(self, manager):
        manager._initialize_filters("dev", "1.0", False, False, False)
        assert manager.context_filter is not None


# ==========================================================
# 5. configure
# ==========================================================

class TestConfigure:
    def test_configure_success_development(self, manager):
        with patch.object(manager, "_initialize_root_logger"), \
             patch.object(manager, "_initialize_specialized_loggers"):
            result = manager.configure(environment="development")
        assert manager.status == ManagerStatus.READY
        assert result["handlers_count"] == 1
        assert result["filters_count"] == 2
        assert manager.is_ready is True

    def test_configure_failure_sets_failed(self, manager):
        manager._formatter_factory.create.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            manager.configure(environment="development")
        assert manager.status == ManagerStatus.FAILED
        assert manager._last_exception is not None


# ==========================================================
# 6. shutdown
# ==========================================================

class TestShutdown:
    def test_shutdown_not_ready(self, manager):
        result = manager.shutdown()
        assert result["closed_handlers"] == 0

    def test_shutdown_ready(self, manager):
        manager._set_status(ManagerStatus.READY)
        manager._handler_factory.close_all.return_value = 3
        result = manager.shutdown()
        assert result["closed_handlers"] == 3
        assert manager.status == ManagerStatus.SHUTDOWN


# ==========================================================
# 7. atomic_reload
# ==========================================================

class TestAtomicReload:
    def test_reload_before_configure_raises(self, manager):
        manager._context_filter = None
        with pytest.raises(RuntimeError):
            manager.atomic_reload()

    def test_reload_failure_returns_error(self, manager):
        manager._context_filter = MagicMock()
        manager._formatter_factory.create.side_effect = RuntimeError("build failed")
        result = manager.atomic_reload(environment="development")
        assert result["success"] is False
        assert result["swapped"] is False
        assert result["error"] is not None

    def test_reload_success(self, manager):
        manager._context_filter = MagicMock()
        result = manager.atomic_reload(environment="development")
        assert result["success"] is True
        assert result["swapped"] is True
        assert result["reload_count"] == 1


# ==========================================================
# 8. health_check & health score
# ==========================================================

class TestHealthCheck:
    def test_health_check_not_ready(self, manager):
        result = manager.health_check()
        assert result["healthy"] is False

    def test_health_check_ready(self, manager):
        manager._set_status(ManagerStatus.READY)
        manager._handler_factory.get_metrics.return_value = {}
        manager._filter_factory.get_metrics.return_value = {}
        manager._logger_factory.get_metrics.return_value = {}
        manager._formatter_factory.get_metrics.return_value = {}
        result = manager.health_check()
        assert result["healthy"] is True
        assert result["health_score"] >= 70

    def test_health_score_with_exception(self, manager):
        manager._last_exception = "err"
        manager._handler_factory.get_metrics.return_value = {}
        manager._filter_factory.get_metrics.return_value = {}
        assert manager._calculate_health_score() == 70

    def test_health_score_handler_issues(self, manager):
        manager._handler_factory.get_metrics.return_value = {"closed_handlers_count": 20}
        manager._filter_factory.get_metrics.return_value = {}
        assert manager._calculate_health_score() == 90

    def test_health_score_filter_cache_issues(self, manager):
        manager._handler_factory.get_metrics.return_value = {}
        manager._filter_factory.get_metrics.return_value = {
            "cache_misses": 10, "cache_hits": 5
        }
        assert manager._calculate_health_score() == 85


# ==========================================================
# 9. uptime_seconds
# ==========================================================

class TestUptime:
    def test_uptime_no_startup(self, manager):
        assert manager.uptime_seconds == 0.0

    def test_uptime_with_startup(self, manager):
        manager._startup_timestamp = datetime.now(timezone.utc).isoformat()
        assert manager.uptime_seconds >= 0.0

    def test_uptime_invalid_timestamp(self, manager):
        manager._startup_timestamp = "invalid"
        assert manager.uptime_seconds == 0.0


# ==========================================================
# 10. Logger access & metadata
# ==========================================================

class TestLoggerAccessAndMetadata:
    def test_get_logger(self, manager):
        manager.get_logger("test")
        manager._logger_factory.get_logger.assert_called_once_with("test")

    def test_context_filter_property(self, manager):
        mock_cf = MagicMock()
        manager._context_filter = mock_cf
        assert manager.context_filter is mock_cf

    def test_get_metrics(self, manager):
        manager._formatter_factory.get_metrics.return_value = {}
        manager._handler_factory.get_metrics.return_value = {}
        manager._filter_factory.get_metrics.return_value = {}
        manager._logger_factory.get_metrics.return_value = {}
        m = manager.get_metrics()
        assert m["version"] == MANAGER_VERSION

    def test_repr(self, manager):
        assert "LoggingManager" in repr(manager)

    def test_version(self, manager):
        assert manager.version == MANAGER_VERSION