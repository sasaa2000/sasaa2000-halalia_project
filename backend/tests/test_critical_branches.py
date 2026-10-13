"""
backend/tests/test_critical_branches.py
اختبارات الفروع الحرجة المكتشفة من term-missing.
"""

from __future__ import annotations

import logging
import sys
import time

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ==========================================================
# 1. Environment — Invalid Value Branch
# ==========================================================

class TestEnvironmentInvalidBranch:
    def test_invalid_env_value_falls_back(self, monkeypatch):
        """APP_ENVIRONMENT=INVALID → development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "INVALID_VALUE")

        from core.configuration.environment import EnvironmentManager
        EnvironmentManager._instance = None

        manager = EnvironmentManager()
        assert manager.current.value == "development"

        EnvironmentManager._instance = None

    def test_env_with_surrounding_spaces(self, monkeypatch):
        """APP_ENVIRONMENT=' production ' → production"""
        monkeypatch.setenv("APP_ENVIRONMENT", "  production  ")

        from core.configuration.environment import EnvironmentManager
        EnvironmentManager._instance = None

        manager = EnvironmentManager()
        assert manager.current.value == "production"

        EnvironmentManager._instance = None

    def test_env_with_newline(self, monkeypatch):
        """APP_ENVIRONMENT='\\nproduction' → production"""
        monkeypatch.setenv("APP_ENVIRONMENT", "\nproduction")

        from core.configuration.environment import EnvironmentManager
        EnvironmentManager._instance = None

        manager = EnvironmentManager()
        assert manager.current.value == "production"

        EnvironmentManager._instance = None


# ==========================================================
# 2. ConfigurationSources — Error Branches
# ==========================================================

class TestSourcesErrorBranches:
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="chmod لا يمنع القراءة على Windows"
    )
    def test_json_source_permission_error(self, tmp_path):
        """JsonSource مع ملف غير قابل للقراءة (Linux/Mac فقط)"""
        from core.configuration.configuration_sources import JsonSource

        restricted = tmp_path / "restricted.json"
        restricted.write_text('{"key": "value"}', encoding="utf-8")
        restricted.chmod(0o000)

        source = JsonSource(restricted)

        try:
            with pytest.raises(Exception):
                source.load()
        finally:
            restricted.chmod(0o644)

    def test_dotenv_source_with_quoted_values(self, tmp_path):
        """DotEnvSource مع قيم مقتبسة"""
        from core.configuration.configuration_sources import DotEnvSource

        env_file = tmp_path / ".env"
        env_file.write_text(
            'KEY1="quoted value"\n'
            "KEY2='single quoted'\n"
            "KEY3=unquoted\n",
            encoding="utf-8"
        )

        source = DotEnvSource(env_file)
        config = source.load()

        assert config["KEY1"] == "quoted value"
        assert config["KEY2"] == "single quoted"
        assert config["KEY3"] == "unquoted"

    def test_dotenv_source_with_equals_in_value(self, tmp_path):
        """DotEnvSource مع = في القيمة"""
        from core.configuration.configuration_sources import DotEnvSource

        env_file = tmp_path / ".env"
        env_file.write_text(
            "DATABASE_URL=postgresql://user:pass@host/db?opt=1\n",
            encoding="utf-8"
        )

        source = DotEnvSource(env_file)
        config = source.load()

        assert config["DATABASE_URL"] == "postgresql://user:pass@host/db?opt=1"


# ==========================================================
# 3. LoggingManager — Error Branches
# ==========================================================

class TestLoggingManagerErrorBranches:
    def test_configure_with_invalid_log_format(self):
        """configure() مع log_format غير صالح → يقع على console"""
        from core.logging.logging_manager import LoggingManager

        LoggingManager._instance = None
        manager = LoggingManager()

        result = manager.configure(
            environment="development",
            log_format="invalid_format",
        )

        assert result is not None
        LoggingManager._instance = None

    def test_shutdown_when_already_shutdown(self):
        """shutdown() مرتين → لا ينهار"""
        from core.logging.logging_manager import LoggingManager

        LoggingManager._instance = None
        manager = LoggingManager()

        result = manager.shutdown()
        assert result["closed_handlers"] == 0

        result = manager.shutdown()
        assert result["closed_handlers"] == 0

        LoggingManager._instance = None


# ==========================================================
# 4. ObservabilityService — Import Error Branch
# ==========================================================

class TestObservabilityImportError:
    def test_initialize_without_config_module(self):
        """initialize() بدون core.configuration → RuntimeError"""
        from core.logging.observability_service import ObservabilityService

        ObservabilityService._instance = None
        service = ObservabilityService()

        original = sys.modules.get("core.configuration")
        sys.modules["core.configuration"] = None

        try:
            with pytest.raises(RuntimeError, match="ConfigurationService"):
                service.initialize(config_service=None)
        finally:
            if original is not None:
                sys.modules["core.configuration"] = original
            else:
                sys.modules.pop("core.configuration", None)

        ObservabilityService._instance = None


# ==========================================================
# 5. LogFilters — Cleanup Branch
# ==========================================================

class TestFilterCleanupBranch:
    def test_rate_limit_cleanup_triggered(self, monkeypatch):
        """RateLimitFilter cleanup يُفعَّل بعد انتهاء bucket_ttl"""
        current_time = [1000.0]
        monkeypatch.setattr(time, "monotonic", lambda: current_time[0])

        from core.logging.log_filters import RateLimitFilter

        fltr = RateLimitFilter(max_calls=10, window_seconds=60.0, bucket_ttl=100.0)

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="test", args=None, exc_info=None,
        )

        fltr.filter(record)
        assert fltr.bucket_count == 1

        # تحريك الوقت لتفعيل cleanup
        current_time[0] = 1361.0
        fltr.filter(record)

        assert fltr.bucket_count >= 1


# ==========================================================
# 6. Metrics — Prometheus Summary Branch
# ==========================================================

class TestPrometheusSummaryBranch:
    def test_prometheus_exports_summary(self):
        """PrometheusExporter مع Summary"""
        from core.monitoring.metrics import MetricRegistry, PrometheusExporter

        MetricRegistry.reset_instance()
        registry = MetricRegistry()

        summary = registry.get_or_create_summary("http_duration")
        summary.observe(0.5)
        summary.observe(1.5)

        exporter = PrometheusExporter()
        output = exporter.export_to_string(registry)

        assert "# TYPE http_duration summary" in output

        MetricRegistry.reset_instance()


# ==========================================================
# 7. ConfigurationCache — TTL Policy (نهائي)
# ==========================================================

class TestCacheTTLFinal:
    def _patch_time(self, monkeypatch, current_time):
        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            lambda: current_time[0],
        )

    def test_ttl_zero_does_not_store(self, monkeypatch):
        """ttl=0 → لا تُخزَّن"""
        current_time = [1000.0]
        self._patch_time(monkeypatch, current_time)

        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)

        cache.set("KEY", "value", ttl=0)

        assert cache.get("KEY") is None
        assert cache.has("KEY") is False
        assert cache.size == 0

    def test_ttl_negative_raises(self, monkeypatch):
        """ttl<0 → ValueError"""
        current_time = [1000.0]
        self._patch_time(monkeypatch, current_time)

        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)

        with pytest.raises(ValueError, match="non-negative"):
            cache.set("KEY", "value", ttl=-1)

        assert cache.size == 0

    def test_ttl_zero_float(self, monkeypatch):
        """ttl=0.0 → لا تُخزَّن"""
        current_time = [1000.0]
        self._patch_time(monkeypatch, current_time)

        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)

        cache.set("KEY", "value", ttl=0.0)

        assert cache.get("KEY") is None
        assert cache.size == 0