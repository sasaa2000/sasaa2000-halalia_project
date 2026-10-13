"""
اختبارات الوحدة لـ EnvironmentManager — v1.0

يغطي:
    ✅ Singleton
    ✅ Auto-Detection من Environment Variable
    ✅ Default Value (development)
    ✅ Invalid Value → Fallback
    ✅ Properties (is_development, is_production, etc.)
    ✅ Composite Properties (is_live, is_local, etc.)
    ✅ validate()
    ✅ set() — يعمل في dev، يرفض في production
    ✅ reload() / reset()
    ✅ supported_environments
    ✅ to_dict()
    ✅ Thread Safety
    ✅ Edge Cases (empty, whitespace, case insensitive)

عدد الاختبارات: 28
"""

from __future__ import annotations

import threading

import pytest

from core.configuration.configuration_models import (
    EnvironmentType,
    SUPPORTED_ENVIRONMENTS,
)
from core.configuration.environment import (
    EnvironmentManager,
    environment,
)


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """إعادة تعيين EnvironmentManager قبل كل اختبار"""
    EnvironmentManager._instance = None
    EnvironmentManager._lock = threading.Lock()
    yield
    EnvironmentManager._instance = None


@pytest.fixture
def env_manager():
    """EnvironmentManager جديد"""
    return EnvironmentManager()


# ==========================================================
# 1. Singleton Tests (2)
# ==========================================================

class TestSingleton:
    def test_singleton(self):
        """نفس المثيل يُرجع دائماً"""
        a = EnvironmentManager()
        b = EnvironmentManager()
        assert a is b

    def test_reset_creates_new_instance(self):
        """إعادة التعيين تنشئ مثيلاً جديداً"""
        a = EnvironmentManager()
        EnvironmentManager._instance = None
        b = EnvironmentManager()
        assert a is not b


# ==========================================================
# 2. Auto-Detection Tests (5)
# ==========================================================

class TestAutoDetection:
    def test_default_is_development(self, monkeypatch):
        """بدون APP_ENVIRONMENT → development"""
        monkeypatch.delenv("APP_ENVIRONMENT", raising=False)
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.DEVELOPMENT

    def test_detect_development(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.DEVELOPMENT

    def test_detect_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.PRODUCTION

    def test_detect_staging(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "staging")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.STAGING

    def test_detect_testing(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "testing")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.TESTING


# ==========================================================
# 3. Invalid Value Handling (3)
# ==========================================================

class TestInvalidValues:
    def test_invalid_value_falls_back_to_default(self, monkeypatch):
        """قيمة غير صالحة → development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "invalid_env")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.DEVELOPMENT

    def test_empty_string_falls_back(self, monkeypatch):
        """سلسلة فارغة → development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.DEVELOPMENT

    def test_whitespace_falls_back(self, monkeypatch):
        """مسافات بيضاء → development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "   ")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.DEVELOPMENT


# ==========================================================
# 4. Case Insensitivity (2)
# ==========================================================

class TestCaseInsensitivity:
    def test_uppercase(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "PRODUCTION")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.PRODUCTION

    def test_mixed_case(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "Staging")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.STAGING


# ==========================================================
# 5. Properties Tests (6)
# ==========================================================

class TestProperties:
    def test_is_development(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()
        assert manager.is_development is True
        assert manager.is_production is False

    def test_is_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.is_production is True
        assert manager.is_development is False

    def test_is_staging(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "staging")
        manager = EnvironmentManager()
        assert manager.is_staging is True

    def test_is_testing(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "testing")
        manager = EnvironmentManager()
        assert manager.is_testing is True

    def test_name_property(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.name == "production"

    def test_id_property(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.id == "PRODUCTION"


# ==========================================================
# 6. Composite Properties (4)
# ==========================================================

class TestCompositeProperties:
    def test_is_live_production(self, monkeypatch):
        """is_live = True في production"""
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.is_live is True

    def test_is_live_staging(self, monkeypatch):
        """is_live = True في staging"""
        monkeypatch.setenv("APP_ENVIRONMENT", "staging")
        manager = EnvironmentManager()
        assert manager.is_live is True

    def test_is_live_development(self, monkeypatch):
        """is_live = False في development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()
        assert manager.is_live is False

    def test_is_local(self, monkeypatch):
        """is_local = True فقط في development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()
        assert manager.is_local is True

    def test_is_local_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.is_local is False

    def test_requires_strict_security(self, monkeypatch):
        """requires_strict_security = True في production و staging"""
        for env in ("production", "staging"):
            monkeypatch.setenv("APP_ENVIRONMENT", env)
            EnvironmentManager._instance = None
            manager = EnvironmentManager()
            assert manager.requires_strict_security is True, f"Failed for {env}"

    def test_supports_hot_reload(self, monkeypatch):
        """supports_hot_reload = True في development و testing"""
        for env in ("development", "testing"):
            monkeypatch.setenv("APP_ENVIRONMENT", env)
            EnvironmentManager._instance = None
            manager = EnvironmentManager()
            assert manager.supports_hot_reload is True, f"Failed for {env}"

    def test_is_safe_for_debug(self, monkeypatch):
        """is_safe_for_debug = False في production"""
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.is_safe_for_debug is False


# ==========================================================
# 7. validate() Tests (2)
# ==========================================================

class TestValidate:
    def test_validate_valid_environment(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        assert manager.validate() is True

    def test_validate_all_supported(self, monkeypatch):
        """جميع البيئات المدعومة صالحة"""
        for env_type in SUPPORTED_ENVIRONMENTS:
            monkeypatch.setenv("APP_ENVIRONMENT", env_type.value)
            EnvironmentManager._instance = None
            manager = EnvironmentManager()
            assert manager.validate() is True, f"Failed for {env_type.value}"


# ==========================================================
# 8. set() Tests (3)
# ==========================================================

class TestSet:
    def test_set_in_development(self, monkeypatch):
        """set() يعمل في development"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()
        manager.set(EnvironmentType.TESTING)
        assert manager.current == EnvironmentType.TESTING

    def test_set_in_production_raises(self, monkeypatch):
        """set() يرفض في production"""
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        with pytest.raises(RuntimeError, match="production"):
            manager.set(EnvironmentType.DEVELOPMENT)

    def test_set_in_staging_raises(self, monkeypatch):
        """set() يرفض في staging"""
        monkeypatch.setenv("APP_ENVIRONMENT", "staging")
        manager = EnvironmentManager()
        with pytest.raises(RuntimeError, match="production"):
            manager.set(EnvironmentType.DEVELOPMENT)


# ==========================================================
# 9. reload() / reset() Tests (2)
# ==========================================================

class TestReloadReset:
    def test_reload_re_detects(self, monkeypatch):
        """reload() يعيد اكتشاف البيئة"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()
        assert manager.current == EnvironmentType.DEVELOPMENT

        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager.reload()
        assert manager.current == EnvironmentType.PRODUCTION

    def test_reset_is_alias_for_reload(self, monkeypatch):
        """reset() يعمل مثل reload()"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()

        monkeypatch.setenv("APP_ENVIRONMENT", "staging")
        manager.reset()
        assert manager.current == EnvironmentType.STAGING


# ==========================================================
# 10. supported_environments Tests (1)
# ==========================================================

class TestSupportedEnvironments:
    def test_supported_environments(self, env_manager):
        """supported_environments يحتوي على جميع البيئات"""
        supported = env_manager.supported_environments
        assert EnvironmentType.DEVELOPMENT in supported
        assert EnvironmentType.PRODUCTION in supported
        assert EnvironmentType.STAGING in supported
        assert EnvironmentType.TESTING in supported
        assert len(supported) == 4


# ==========================================================
# 11. to_dict() Tests (2)
# ==========================================================

class TestToDict:
    def test_to_dict_structure(self, monkeypatch):
        """to_dict() يُرجع جميع المفاتيح الأساسية"""
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        result = manager.to_dict()

        expected_keys = {
            "id", "current", "is_production", "is_development",
            "is_testing", "is_staging", "is_live", "is_local",
            "requires_strict_security", "supports_hot_reload",
            "env_var_name",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_to_dict_values(self, monkeypatch):
        """to_dict() يُرجع قيماً صحيحة"""
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        result = manager.to_dict()

        assert result["current"] == "production"
        assert result["is_production"] is True
        assert result["is_development"] is False
        assert result["is_live"] is True
        assert result["requires_strict_security"] is True


# ==========================================================
# 12. Thread Safety Tests (2)
# ==========================================================

class TestThreadSafety:
    def test_concurrent_access(self, monkeypatch):
        """الوصول المتزامن آمن"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()

        results = []
        errors = []

        def worker():
            try:
                for _ in range(100):
                    results.append(manager.current)
                    _ = manager.is_production
                    _ = manager.name
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 1000
        assert all(r == EnvironmentType.DEVELOPMENT for r in results)

    def test_concurrent_set_and_read(self, monkeypatch):
        """set() و get() معاً آمنان"""
        monkeypatch.setenv("APP_ENVIRONMENT", "development")
        manager = EnvironmentManager()

        errors = []
        valid_states = {
            EnvironmentType.DEVELOPMENT,
            EnvironmentType.TESTING,
        }

        def reader():
            try:
                for _ in range(50):
                    state = manager.current
                    assert state in valid_states, f"Invalid state: {state}"
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for _ in range(50):
                    manager.set(EnvironmentType.TESTING)
                    manager.set(EnvironmentType.DEVELOPMENT)
            except Exception as e:
                errors.append(e)

        threads = (
            [threading.Thread(target=reader) for _ in range(5)] +
            [threading.Thread(target=writer) for _ in range(2)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ==========================================================
# 13. Global Instance Tests (1)
# ==========================================================

class TestGlobalInstance:
    def test_global_instance_exists(self):
        """المثيل العام موجود"""
        assert environment is not None
        assert isinstance(environment, EnvironmentManager)


# ==========================================================
# 14. repr Tests (1)
# ==========================================================

class TestRepr:
    def test_repr(self, monkeypatch):
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        manager = EnvironmentManager()
        repr_str = repr(manager)
        assert "EnvironmentManager" in repr_str
        assert "production" in repr_str