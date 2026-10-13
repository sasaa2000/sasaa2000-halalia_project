"""
اختبارات سد فجوات Coverage — v2.2

التحسينات المطبقة:
    ✅ try/except/else بدلاً من except Exception العامة
    ✅ test_invalid_regex_pattern يتحقق من is_valid False
    ✅ cleanup يتحقق من has()
    ✅ تنظيف Handlers بعد اختبارات Logging
    ✅ MagicMock مع spec لمنع أسماء غير موجودة
    ✅ اختبارات إضافية: concurrent cache, validator None/empty, overwrite
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ==========================================================
# 1. ConfigurationService — Error Recovery
# ==========================================================

class TestConfigurationServiceErrorRecovery:
    def test_initialize_failure_raises_clean_error(self):
        from core.configuration.configuration_service import ConfigurationService

        service = ConfigurationService(base_path=Path("/nonexistent/path"))
        try:
            service.initialize()
        except RuntimeError as e:
            assert "ConfigurationService" in str(e) or "not available" in str(e)
        else:
            assert service.is_initialized is True

    def test_get_after_failed_initialize_raises(self):
        from core.configuration.configuration_service import ConfigurationService

        service = ConfigurationService()
        with pytest.raises(RuntimeError):
            service.get("ANY_KEY")

    def test_health_check_before_initialize(self):
        from core.configuration.configuration_service import ConfigurationService

        service = ConfigurationService()
        health = service.health_check()
        assert health["healthy"] is False


# ==========================================================
# 2. Reload — Atomic Behavior
# ==========================================================

class TestReloadAtomicBehavior:
    def _make_service(self):
        from core.configuration.configuration_service import ConfigurationService
        from core.configuration.configuration_cache import ConfigurationCache
        from core.configuration.configuration_sources import ConfigurationSourceManager
        from core.configuration.configuration_profiles import ProfileManager
        from core.configuration.configuration_validator import ConfigurationValidator

        service = ConfigurationService(base_path=Path("/tmp/test"))
        service._initialized = True
        service._final_config = {"KEY": "original"}
        service._raw_config = {"KEY": "original"}

        service._cache = MagicMock(spec=ConfigurationCache)
        service._cache.get.return_value = None

        service._sources = MagicMock(spec=ConfigurationSourceManager)
        service._sources.load_all.return_value = {"KEY": "reloaded"}

        service._profiles = MagicMock(spec=ProfileManager)
        service._profiles.apply_active_profile.side_effect = lambda c: c

        service._validator = MagicMock(spec=ConfigurationValidator)
        mock_report = MagicMock()
        mock_report.is_valid = True
        service._validator.validate.return_value = mock_report

        service._environment = MagicMock()
        service._environment.name = "development"
        return service

    def test_reload_never_returns_invalid_state(self):
        service = self._make_service()
        observed = []
        errors = []

        def reader():
            try:
                for _ in range(50):
                    val = service.get("KEY")
                    if val is not None:
                        observed.append(val)
            except Exception as e:
                errors.append(e)

        def reloader():
            try:
                for _ in range(10):
                    service.reload()
            except Exception:
                pass

        threads = (
            [threading.Thread(target=reader) for _ in range(3)] +
            [threading.Thread(target=reloader) for _ in range(1)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        valid_values = {"original", "reloaded"}
        for val in observed:
            assert val in valid_values, f"Unexpected value: {val}"

    def test_reload_failure_preserves_get_behavior(self):
        service = self._make_service()
        service._sources.load_all.side_effect = RuntimeError("Source failed")

        with pytest.raises(RuntimeError):
            service.reload()

        assert service.get("KEY") == "original"


# ==========================================================
# 3. Validator — Exception Handling
# ==========================================================

class TestValidatorExceptionHandling:
    def _base_config(self, **extra):
        return {
            "TELEGRAM_BOT_TOKEN": "1234567890" * 4,
            "SYSTEM_MASTER_PIN": "1234",
            "ENVIRONMENT": "development",
            "DATABASE_URL": "postgresql://localhost/db",
            **extra,
        }

    def _make_validator(self):
        from core.configuration.configuration_schema import ConfigurationSchema
        from core.configuration.configuration_validator import ConfigurationValidator
        return ConfigurationSchema(name="test"), ConfigurationValidator

    def test_custom_validator_exception_does_not_crash(self):
        from core.configuration.configuration_models import ValidationRule, ValidationRuleType
        schema, Validator = self._make_validator()
        validator = Validator(schema=schema)
        schema.add_rule(ValidationRule(id="R1", field="DATA", rule_type=ValidationRuleType.CUSTOM))

        def broken_validator(value):
            raise ValueError("Validator crashed!")
        schema.add_custom_validator("DATA", broken_validator)

        report = validator.validate(self._base_config(DATA="anything"))
        assert report is not None
        assert isinstance(report.is_valid, bool)

    def test_invalid_regex_pattern_does_not_crash(self):
        from core.configuration.configuration_models import ValidationRule, ValidationRuleType
        schema, Validator = self._make_validator()
        validator = Validator(schema=schema)
        schema.add_rule(ValidationRule(
            id="R1", field="DATA",
            rule_type=ValidationRuleType.PATTERN,
            value=r"[invalid(regex",
        ))

        report = validator.validate(self._base_config(DATA="test"))
        assert report is not None
        # ✅ Regex غير صالح → خطأ مُسجّل وليس انهياراً
        assert report.is_valid is False

    def test_validator_with_empty_dict(self):
        schema, Validator = self._make_validator()
        validator = Validator(schema=schema)
        report = validator.validate({})
        # القواعد الافتراضية المطلوبة تفشل → غير صالح
        assert report.is_valid is False

    def test_validator_with_none_value(self):
        from core.configuration.configuration_models import ValidationRule, ValidationRuleType
        schema, Validator = self._make_validator()
        validator = Validator(schema=schema)
        schema.add_rule(ValidationRule(id="R1", field="NULL_FIELD", rule_type=ValidationRuleType.REQUIRED))
        report = validator.validate(self._base_config(NULL_FIELD=None))
        assert report.is_valid is False


# ==========================================================
# 4. Sources — I/O Failures
# ==========================================================

class TestSourcesIOFailures:
    def test_json_source_with_invalid_json(self, tmp_path):
        from core.configuration.configuration_sources import JsonSource
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid}", encoding="utf-8")
        with pytest.raises(Exception):
            JsonSource(bad_file).load()

    def test_json_source_with_array(self, tmp_path):
        from core.configuration.configuration_sources import JsonSource
        array_file = tmp_path / "array.json"
        array_file.write_text("[1,2,3]", encoding="utf-8")
        with pytest.raises(ValueError):
            JsonSource(array_file).load()

    def test_file_source_unreadable(self, tmp_path):
        from core.configuration.configuration_sources import JsonSource
        source = JsonSource(tmp_path / "nonexistent" / "file.json")
        assert source.is_available() is False

    def test_dotenv_with_unicode(self, tmp_path):
        from core.configuration.configuration_sources import DotEnvSource
        env_file = tmp_path / ".env"
        env_file.write_text("APP_NAME=حَلَالِيّة\n", encoding="utf-8")
        config = DotEnvSource(env_file).load()
        assert config["APP_NAME"] == "حَلَالِيّة"


# ==========================================================
# 5. Cache — TTL & Concurrency & Overwrite
# ==========================================================

class TestCacheTTLEdgeCases:
    def _patch_time(self, monkeypatch, current_time):
        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            lambda: current_time[0],
        )

    def test_ttl_zero(self, monkeypatch):
        current_time = [1000.0]
        self._patch_time(monkeypatch, current_time)
        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)
        cache.set("KEY", "value", ttl=0)
        assert cache.get("KEY") is None
        assert cache.size == 0

    def test_ttl_negative(self, monkeypatch):
        current_time = [1000.0]
        self._patch_time(monkeypatch, current_time)
        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)
        with pytest.raises(ValueError):
            cache.set("KEY", "value", ttl=-5)
        assert cache.size == 0

    def test_cleanup_with_monkeypatch(self, monkeypatch):
        current_time = [1000.0]
        self._patch_time(monkeypatch, current_time)
        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=5.0)
        cache.set("SHORT", "v", ttl=1.0)
        cache.set("LONG", "v", ttl=100.0)

        current_time[0] = 1002.0
        removed = cache.cleanup()

        assert removed == 1
        assert cache.size == 1
        # ✅ التحقق عبر has() أيضاً
        assert cache.has("SHORT") is False
        assert cache.has("LONG") is True

    def test_cache_overwrite(self):
        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)
        cache.set("K", "v1")
        cache.set("K", "v2")
        assert cache.get("K") == "v2"
        assert cache.size == 1

    def test_concurrent_cache_write(self):
        from core.configuration.configuration_cache import ConfigurationCache
        cache = ConfigurationCache(default_ttl=300.0)
        errors = []

        def writer(tid):
            try:
                for i in range(50):
                    cache.set(f"K{tid}_{i}", f"V{tid}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert cache.size == 250


# ==========================================================
# 6. Logging — Shutdown Paths (مع تنظيف Handlers)
# ==========================================================

class TestLoggingShutdownPaths:
    @pytest.fixture(autouse=True)
    def clean_handlers(self):
        yield
        logging.getLogger().handlers.clear()

    def test_shutdown_when_not_initialized(self):
        from core.logging.logging_manager import LoggingManager
        LoggingManager._instance = None
        manager = LoggingManager()
        result = manager.shutdown()
        assert result["closed_handlers"] == 0
        LoggingManager._instance = None

    def test_double_shutdown(self):
        from core.logging.logging_manager import LoggingManager
        LoggingManager._instance = None
        manager = LoggingManager()
        manager.shutdown()
        result = manager.shutdown()
        assert result["closed_handlers"] == 0
        LoggingManager._instance = None


# ==========================================================
# 7. Metrics — Defensive Branches
# ==========================================================

class TestMetricsDefensiveBranches:
    def test_counter_with_zero_amount(self):
        from core.monitoring.metrics import Counter
        counter = Counter("test")
        counter.inc(0)
        assert counter.get() == 0.0

    def test_gauge_with_zero(self):
        from core.monitoring.metrics import Gauge
        gauge = Gauge("test")
        gauge.set(0)
        assert gauge.get() == 0.0

    def test_histogram_with_negative_value(self):
        from core.monitoring.metrics import Histogram
        histogram = Histogram("test")
        histogram.observe(-1.0)
        data = list(histogram.collect()["data"].values())[0]
        assert data["count"] == 1

    def test_summary_with_single_sample(self):
        from core.monitoring.metrics import Summary
        summary = Summary("test")
        summary.observe(42.0)
        data = list(summary.collect()["data"].values())[0]
        assert data["count"] == 1
        for q_val in data["quantiles"].values():
            assert q_val == 42.0

    def test_metric_with_empty_name_raises(self):
        from core.monitoring.metrics import Counter, MetricRegistrationError
        with pytest.raises(MetricRegistrationError):
            Counter("")

    def test_registry_get_nonexistent_raises(self):
        from core.monitoring.metrics import MetricRegistry, MetricNotFoundError
        MetricRegistry.reset_instance()
        registry = MetricRegistry()
        with pytest.raises(MetricNotFoundError):
            registry.get("nonexistent")
        MetricRegistry.reset_instance()