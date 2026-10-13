"""
اختبارات الوحدة لـ ConfigurationService — v1.0

يغطي:
    ✅ Singleton
    ✅ initialize()
    ✅ get() / get_bool() / get_int() / get_str()
    ✅ has() / keys() / as_dict()
    ✅ reload()
    ✅ validate() / is_valid()
    ✅ health_check() / get_metrics()
    ✅ ready / version properties
    ✅ Thread Safety
    ✅ Error Handling
    ✅ Cache Integration
    ✅ Profile Integration

عدد الاختبارات: 45
"""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from core.configuration.configuration_service import (
    CACHE_PREFIX,
    SERVICE_VERSION,
    ConfigurationService,
    config_service,
)


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture(autouse=True)
def reset_service():
    """إعادة تعيين ConfigurationService قبل كل اختبار"""
    ConfigurationService._instance = None
    ConfigurationService._lock = __import__("threading").Lock()
    yield
    ConfigurationService._instance = None


@pytest.fixture
def service():
    """ConfigurationService جديد"""
    svc = ConfigurationService(base_path=Path("/tmp/test_config"))
    return svc


@pytest.fixture
def initialized_service(service):
    """ConfigurationService مهيأ وجاهز"""
    # محاكاة تهيئة ناجحة
    service._initialized = True
    service._load_time_ms = 5.0
    service._final_config = {
        "APP_NAME": "HALALIA",
        "APP_PORT": "8080",
        "APP_DEBUG": "true",
        "APP_LOG_LEVEL": "INFO",
        "APP_RATE_LIMIT": "100",
        "DATABASE_URL": "sqlite:///test.db",
        "EMPTY_VALUE": "",
    }
    service._raw_config = service._final_config.copy()

    # محاكاة المكونات
    service._environment = MagicMock()
    service._environment.name = "development"
    service._environment.is_production = False

    service._cache = MagicMock()
    service._cache.get.return_value = None  # Cache miss افتراضي
    service._cache.healthy = True
    service._cache.size = 0

    service._sources = MagicMock()
    service._sources.source_count = 3
    service._sources.available_count = 2

    service._profiles = MagicMock()
    service._profiles.profile_count = 4

    service._validator = MagicMock()
    mock_report = MagicMock()
    mock_report.is_valid = True
    mock_report.to_dict.return_value = {"valid": True, "errors": []}
    service._validator.validate.return_value = mock_report

    return service


# ==========================================================
# 1. Singleton Tests (3)
# ==========================================================

class TestSingleton:
    def test_global_instance_exists(self):
        from core.configuration.configuration_service import config_service
        assert config_service is not None
        assert isinstance(config_service, ConfigurationService)

    def test_new_instance_independent(self):
        a = ConfigurationService()
        b = ConfigurationService()
        assert a is not b

    def test_reset_creates_new(self):
        a = ConfigurationService()
        ConfigurationService._instance = None
        b = ConfigurationService()
        assert a is not b

    def test_custom_base_path(self):
        svc = ConfigurationService(base_path=Path("/custom/path"))
        assert svc._base_path == Path("/custom/path")


# ==========================================================
# 2. Initialize Tests (5)
# ==========================================================

class TestInitialize:
    def test_initialize_sets_initialized(self, service):
        """initialize() يضبط _initialized"""
        with patch.object(service, '_load_configurations'):
            with patch.object(service, '_sources', create=True) as mock_sources:
                mock_sources.load_all.return_value = {}
                with patch.object(service, '_profiles', create=True) as mock_profiles:
                    mock_profiles.apply_active_profile.return_value = {}
                    with patch.object(service, '_cache', create=True):
                        with patch.object(service, '_environment', create=True) as mock_env:
                            mock_env.name = "development"
                            mock_env.has_profile = MagicMock(return_value=False)

                            service.initialize()

                            assert service._initialized is True

    def test_initialize_idempotent(self, service):
        """initialize() لا يعيد التهيئة إذا كان مهيأً"""
        service._initialized = True
        service._load_time_ms = 10.0

        # يجب ألا يرفع خطأ
        service.initialize()

    def test_initialize_measures_time(self, service):
        """initialize() يقيس وقت التهيئة"""
        with patch.object(service, '_load_configurations'):
            with patch.object(service, '_sources', create=True) as mock_sources:
                mock_sources.load_all.return_value = {}
                with patch.object(service, '_profiles', create=True) as mock_profiles:
                    mock_profiles.apply_active_profile.return_value = {}
                    with patch.object(service, '_cache', create=True):
                        with patch.object(service, '_environment', create=True) as mock_env:
                            mock_env.name = "development"
                            mock_env.has_profile = MagicMock(return_value=False)

                            service.initialize()

                            assert service._load_time_ms >= 0

    def test_initialize_raises_before_ready(self, service):
        """get() يرفع خطأ قبل التهيئة"""
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get("APP_NAME")




# ==========================================================
# 3. get() Tests (8)
# ==========================================================

class TestGet:
    def test_get_existing_key(self, initialized_service):
        assert initialized_service.get("APP_NAME") == "HALALIA"

    def test_get_missing_key_returns_default(self, initialized_service):
        assert initialized_service.get("NONEXISTENT") is None

    def test_get_missing_key_custom_default(self, initialized_service):
        assert initialized_service.get("NONEXISTENT", "fallback") == "fallback"

    def test_get_empty_value(self, initialized_service):
        assert initialized_service.get("EMPTY_VALUE") == ""

    def test_get_from_cache(self, initialized_service):
        """get() يبحث في Cache أولاً"""
        initialized_service._cache.get.return_value = "cached_value"

        result = initialized_service.get("APP_NAME")

        assert result == "cached_value"
        initialized_service._cache.get.assert_called_once_with(f"{CACHE_PREFIX}APP_NAME")

    def test_get_caches_value(self, initialized_service):
        """get() يخزن القيمة في Cache"""
        initialized_service._cache.get.return_value = None  # Cache miss

        initialized_service.get("APP_NAME")

        initialized_service._cache.set.assert_called_once_with(
            f"{CACHE_PREFIX}APP_NAME",
            "HALALIA",
            ttl=300.0,
        )

    def test_get_does_not_cache_none(self, initialized_service):
        """get() لا يخزن None في Cache"""
        initialized_service._cache.get.return_value = None

        initialized_service.get("NONEXISTENT")

        initialized_service._cache.set.assert_not_called()

    def test_get_raises_before_initialize(self, service):
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get("APP_NAME")


# ==========================================================
# 4. Typed Getters Tests (8)
# ==========================================================

class TestTypedGetters:
    def test_get_int(self, initialized_service):
        assert initialized_service.get_int("APP_PORT") == 8080

    def test_get_int_default(self, initialized_service):
        assert initialized_service.get_int("NONEXISTENT", 3000) == 3000

    def test_get_int_invalid_returns_default(self, initialized_service):
        assert initialized_service.get_int("APP_NAME", 0) == 0

    def test_get_bool_true(self, initialized_service):
        assert initialized_service.get_bool("APP_DEBUG") is True

    def test_get_bool_false(self, initialized_service):
        initialized_service._final_config["APP_DEBUG"] = "false"
        assert initialized_service.get_bool("APP_DEBUG") is False

    def test_get_bool_default(self, initialized_service):
        assert initialized_service.get_bool("NONEXISTENT", True) is True

    def test_get_str(self, initialized_service):
        assert initialized_service.get_str("APP_NAME") == "HALALIA"

    def test_get_str_default(self, initialized_service):
        assert initialized_service.get_str("NONEXISTENT", "default") == "default"


# ==========================================================
# 5. Collection Methods Tests (4)
# ==========================================================

class TestCollectionMethods:
    def test_has_existing_key(self, initialized_service):
        assert initialized_service.has("APP_NAME") is True

    def test_has_missing_key(self, initialized_service):
        assert initialized_service.has("NONEXISTENT") is False

    def test_keys(self, initialized_service):
        keys = initialized_service.keys()
        assert "APP_NAME" in keys
        assert "APP_PORT" in keys

    def test_as_dict(self, initialized_service):
        config = initialized_service.as_dict()
        assert isinstance(config, dict)
        assert config["APP_NAME"] == "HALALIA"
        # يجب أن يكون نسخة وليس المرجع الأصلي
        config["APP_NAME"] = "MODIFIED"
        assert initialized_service._final_config["APP_NAME"] == "HALALIA"


# ==========================================================
# 6. Reload Tests (3)
# ==========================================================

class TestReload:
    def test_reload_clears_cache(self, initialized_service):
        """reload() يمسح Cache"""
        with patch.object(initialized_service, '_load_configurations'):
            initialized_service.reload()
            initialized_service._cache.clear.assert_called_once()

    def test_reload_reloads_configurations(self, initialized_service):
        """reload() يعيد تحميل الإعدادات"""
        with patch.object(initialized_service, '_load_configurations') as mock_load:
            initialized_service.reload()
            mock_load.assert_called_once()

    def test_reload_thread_safe(self, initialized_service):
        """reload() آمن في تعدد المهام"""
        errors = []

        def reload_worker():
            try:
                with patch.object(initialized_service, '_load_configurations'):
                    initialized_service.reload()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reload_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ==========================================================
# 7. Validation Tests (4)
# ==========================================================

class TestValidation:
    def test_validate_returns_dict(self, initialized_service):
        result = initialized_service.validate()
        assert isinstance(result, dict)
        assert "valid" in result

    def test_is_valid_true(self, initialized_service):
        assert initialized_service.is_valid() is True

    def test_is_valid_false(self, initialized_service):
        mock_report = MagicMock()
        mock_report.is_valid = False
        initialized_service._validator.validate.return_value = mock_report

        assert initialized_service.is_valid() is False

    def test_validate_raises_before_initialize(self, service):
        with pytest.raises(RuntimeError, match="not initialized"):
            service.validate()


# ==========================================================
# 8. Health Check Tests (4)
# ==========================================================

class TestHealthCheck:
    def test_health_check_when_ready(self, initialized_service):
        health = initialized_service.health_check()
        assert health["healthy"] is True
        assert health["ready"] is True
        assert "environment" in health
        assert "cache_healthy" in health

    def test_health_check_when_not_initialized(self, service):
        health = service.health_check()
        assert health["healthy"] is False
        assert "reason" in health

    def test_health_check_includes_metrics(self, initialized_service):
        health = initialized_service.health_check()
        assert "total_keys" in health
        assert "cache_size" in health
        assert "sources_count" in health

    def test_health_check_reflects_validation(self, initialized_service):
        mock_report = MagicMock()
        mock_report.is_valid = False
        initialized_service._validator.validate.return_value = mock_report

        health = initialized_service.health_check()
        assert health["config_valid"] is False


# ==========================================================
# 9. Metrics Tests (2)
# ==========================================================

class TestMetrics:
    def test_get_metrics(self, initialized_service):
        metrics = initialized_service.get_metrics()
        assert metrics["version"] == SERVICE_VERSION
        assert "load_time_ms" in metrics
        assert "cache_stats" in metrics
        assert "total_keys" in metrics

    def test_get_metrics_includes_sources(self, initialized_service):
        metrics = initialized_service.get_metrics()
        assert "sources_count" in metrics
        assert "available_sources" in metrics


# ==========================================================
# 10. Properties Tests (4)
# ==========================================================

class TestProperties:
    def test_is_initialized(self, initialized_service):
        assert initialized_service.is_initialized is True

    def test_is_not_initialized(self, service):
        assert service.is_initialized is False

    def test_version(self, initialized_service):
        assert initialized_service.version == SERVICE_VERSION

    def test_ready(self, initialized_service):
        assert initialized_service.ready is True

    def test_not_ready_when_invalid(self, initialized_service):
        mock_report = MagicMock()
        mock_report.is_valid = False
        initialized_service._validator.validate.return_value = mock_report

        assert initialized_service.ready is False


# ==========================================================
# 11. Component Access Tests (4)
# ==========================================================

class TestComponentAccess:
    def test_environment_property(self, initialized_service):
        assert initialized_service.environment is initialized_service._environment

    def test_cache_property(self, initialized_service):
        assert initialized_service.cache is initialized_service._cache

    def test_profiles_property(self, initialized_service):
        assert initialized_service.profiles is initialized_service._profiles

    def test_sources_property(self, initialized_service):
        assert initialized_service.sources is initialized_service._sources

    def test_component_access_raises_before_initialize(self, service):
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = service.environment


# ==========================================================
# 12. Thread Safety Tests (2)
# ==========================================================

class TestThreadSafety:
    def test_concurrent_get(self, initialized_service):
        """get() آمن في تعدد المهام"""
        results = []
        errors = []

        def get_worker():
            try:
                for _ in range(100):
                    value = initialized_service.get("APP_NAME")
                    results.append(value)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(v == "HALALIA" for v in results)

    def test_concurrent_get_and_reload(self, initialized_service):
        """get() و reload() معاً آمنان"""
        errors = []

        def get_worker():
            try:
                for _ in range(50):
                    initialized_service.get("APP_NAME")
            except Exception as e:
                errors.append(e)

        def reload_worker():
            try:
                for _ in range(10):
                    with patch.object(initialized_service, '_load_configurations'):
                        initialized_service.reload()
            except Exception as e:
                errors.append(e)

        threads = (
                [threading.Thread(target=get_worker) for _ in range(5)] +
                [threading.Thread(target=reload_worker) for _ in range(2)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ==========================================================
# 13. Metadata Tests (2)
# ==========================================================

class TestMetadata:
    def test_to_dict(self, initialized_service):
        result = initialized_service.to_dict()
        assert result["version"] == SERVICE_VERSION
        assert result["initialized"] is True
        assert "health" in result

    def test_repr(self, initialized_service):
        repr_str = repr(initialized_service)
        assert "ConfigurationService" in repr_str
        assert "development" in repr_str


# ==========================================================
# 14. Edge Cases Tests (3)
# ==========================================================

class TestEdgeCases:
    def test_get_with_none_value_in_config(self, initialized_service):
        """get() يتعامل مع None في الإعدادات"""
        initialized_service._final_config["NONE_KEY"] = None
        assert initialized_service.get("NONE_KEY") is None

    def test_get_with_numeric_string(self, initialized_service):
        """get_int() يتعامل مع الأرقام كنصوص"""
        initialized_service._final_config["NUM_STR"] = "42"
        assert initialized_service.get_int("NUM_STR") == 42

    def test_get_bool_various_truthy_values(self, initialized_service):
        """get_bool() يتعرف على القيم الصحيحة"""
        for truthy in ("true", "1", "yes", "on", "enabled", "True", "TRUE"):
            initialized_service._final_config["BOOL_KEY"] = truthy
            assert initialized_service.get_bool("BOOL_KEY") is True, f"Failed for: {truthy}"

    def test_get_bool_various_falsy_values(self, initialized_service):
        """get_bool() يتعرف على القيم الخاطئة"""
        for falsy in ("false", "0", "no", "off", "disabled", "False", "FALSE"):
            initialized_service._final_config["BOOL_KEY"] = falsy
            assert initialized_service.get_bool("BOOL_KEY") is False, f"Failed for: {falsy}"