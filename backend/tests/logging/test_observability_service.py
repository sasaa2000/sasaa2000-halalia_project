"""
اختبارات الوحدة لـ ObservabilityService — v1.0

يغطي:
    ✅ Singleton
    ✅ initialize() مع ConfigurationService
    ✅ initialize() بدون ConfigurationService (خطأ)
    ✅ shutdown()
    ✅ reload()
    ✅ request_context()
    ✅ health_check()
    ✅ get_metrics()
    ✅ Specialized Loggers
    ✅ Metrics Integration
    ✅ حالات الخطأ
    ✅ Atomic Reload

يستخدم:
    - unittest.mock لعزل الاعتماديات
    - pytest-mock (اختياري)
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from core.logging.observability_service import (
    SERVICE_VERSION,
    ObservabilityService,
    ServiceStatus,
)
from core.logging.logging_manager import ManagerStatus


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture(autouse=True)
def reset_service():
    """إعادة تعيين ObservabilityService قبل كل اختبار"""
    ObservabilityService._instance = None
    ObservabilityService._lock = __import__("threading").Lock()
    yield
    ObservabilityService._instance = None


@pytest.fixture
def service():
    """ObservabilityService جديد"""
    return ObservabilityService()


@pytest.fixture
def mock_config_service():
    """ConfigurationService وهمي"""
    config = MagicMock()

    # Environment
    mock_env = MagicMock()
    mock_env.name = "development"
    type(config).environment = PropertyMock(return_value=mock_env)

    # get()
    config.get.side_effect = lambda key, default=None: {
        "APP_LOG_LEVEL": "INFO",
        "APP_LOG_FORMAT": "console",
        "APP_LOG_DIR": "runtime/logs",
        "APP_LOG_ROTATION": "none",
        "APP_VERSION": "1.0.0",
    }.get(key, default)

    # get_bool()
    config.get_bool.side_effect = lambda key, default=False: {
        "APP_LOG_JSON": False,
        "APP_LOG_SENSITIVE_MASKING": True,
        "APP_LOG_RATE_LIMIT": False,
        "APP_LOG_INCLUDE_PII": False,
    }.get(key, default)

    # get_int()
    config.get_int.side_effect = lambda key, default=0: {
        "APP_LOG_MAX_SIZE": 10485760,
        "APP_LOG_BACKUPS": 5,
    }.get(key, default)

    return config


# ==========================================================
# 1. Singleton Tests
# ==========================================================

class TestSingleton:
    def test_singleton(self):
        a = ObservabilityService()
        b = ObservabilityService()
        assert a is b

    def test_reset_creates_new(self):
        a = ObservabilityService()
        ObservabilityService._instance = None
        b = ObservabilityService()
        assert a is not b


# ==========================================================
# 2. Initialize Tests
# ==========================================================

class TestInitialize:
    def test_initialize_with_config(self, service, mock_config_service):
        """initialize() يعمل مع ConfigurationService"""
        with patch.object(service._manager, 'configure') as mock_configure:
            mock_configure.return_value = {"status": "ready"}

            result = service.initialize(mock_config_service)

            mock_configure.assert_called_once()
            assert result["status"] is not None

    def test_initialize_without_config_raises(self, service):
        """initialize() بدون ConfigurationService يرفع خطأ"""
        with patch.dict('sys.modules', {'core.configuration': None}):
            with pytest.raises(RuntimeError, match="ConfigurationService"):
                service.initialize(None)

    def test_initialize_reads_config_correctly(self, service, mock_config_service):
        """initialize() يقرأ الإعدادات بشكل صحيح"""
        with patch.object(service._manager, 'configure') as mock_configure:
            mock_configure.return_value = {}

            service.initialize(mock_config_service)

            # التحقق من أن configure() استُدعي بالإعدادات الصحيحة
            call_kwargs = mock_configure.call_args[1]
            assert call_kwargs["environment"] == "development"
            assert call_kwargs["log_level"] == "INFO"
            assert call_kwargs["log_format"] == "console"

    def test_initialize_freezes_metrics(self, service, mock_config_service):
        """initialize() يجمد MetricsService"""
        with patch.object(service._manager, 'configure'):
            with patch.object(service._metrics, 'freeze') as mock_freeze:
                service.initialize(mock_config_service)
                mock_freeze.assert_called_once()

    def test_initialize_idempotent(self, service, mock_config_service):
        """initialize() يمكن استدعاؤه عدة مرات"""
        with patch.object(service._manager, 'configure') as mock_configure:
            mock_configure.return_value = {}

            service.initialize(mock_config_service)
            service.initialize(mock_config_service)

            # يجب أن يُستدعى configure() مرتين (لا يوجد idempotent check حالياً)
            assert mock_configure.call_count == 2


# ==========================================================
# 3. Shutdown Tests
# ==========================================================

class TestShutdown:
    def test_shutdown_calls_manager(self, service):
        """shutdown() يستدعي manager.shutdown()"""
        with patch.object(service._manager, 'shutdown') as mock_shutdown:
            mock_shutdown.return_value = {"closed_handlers": 2}

            result = service.shutdown()

            mock_shutdown.assert_called_once()
            assert result["closed_handlers"] == 2

    def test_shutdown_unfreezes_metrics(self, service):
        """shutdown() يفك تجميد MetricsService"""
        with patch.object(service._manager, 'shutdown'):
            with patch.object(service._metrics, 'unfreeze') as mock_unfreeze:
                service.shutdown()
                mock_unfreeze.assert_called_once()


# ==========================================================
# 4. Reload Tests
# ==========================================================

class TestReload:
    def test_reload_calls_atomic_reload(self, service, mock_config_service):
        """reload() يستدعي atomic_reload()"""
        with patch.object(service._manager, 'atomic_reload') as mock_reload:
            mock_reload.return_value = {"success": True}

            with patch.object(service._metrics, 'unfreeze'):
                with patch.object(service._metrics, 'freeze'):
                    result = service.reload(mock_config_service)

            mock_reload.assert_called_once()
            assert result["success"] is True

    def test_reload_without_config_raises(self, service):
        """reload() بدون ConfigurationService يرفع خطأ"""
        with patch.dict('sys.modules', {'core.configuration': None}):
            with pytest.raises(RuntimeError, match="ConfigurationService"):
                service.reload(None)


# ==========================================================
# 5. Status Tests
# ==========================================================

class TestStatus:
    def test_status_delegates_to_manager(self, service):
        """status يعكس حالة Manager"""
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            assert service.status == ManagerStatus.READY

    def test_is_ready(self, service):
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            assert service.is_ready is True

    def test_is_not_ready(self, service):
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.NOT_INITIALIZED
        ):
            assert service.is_ready is False

    def test_is_initialized(self, service):
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            assert service.is_initialized is True


# ==========================================================
# 6. Logger Access Tests
# ==========================================================

class TestLoggerAccess:
    def test_get_logger_when_ready(self, service):
        """get_logger() يعمل عندما يكون النظام جاهزاً"""
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            with patch.object(service._manager, 'get_logger') as mock_get:
                mock_logger = MagicMock()
                mock_get.return_value = mock_logger

                result = service.get_logger("test")

                mock_get.assert_called_once_with("test")
                assert result is mock_logger

    def test_get_logger_when_not_ready_raises(self, service):
        """get_logger() يرفع خطأ عندما يكون النظام غير جاهز"""
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.NOT_INITIALIZED
        ):
            with pytest.raises(RuntimeError, match="not ready"):
                service.get_logger("test")

    def test_specialized_loggers(self, service):
        """الوصول للمسجلات المتخصصة"""
        mock_logger = MagicMock()

        with patch.object(
                type(service._manager._logger_factory), 'system',
                new_callable=PropertyMock,
                return_value=mock_logger
        ):
            assert service.system is mock_logger


# ==========================================================
# 7. Context Management Tests
# ==========================================================

class TestContextManagement:
    def test_set_request_id(self, service):
        """set_request_id() يفوض لـ ContextFilter"""
        mock_cf = MagicMock()
        with patch.object(
                type(service._manager), 'context_filter',
                new_callable=PropertyMock,
                return_value=mock_cf
        ):
            service.set_request_id("req-123")
            mock_cf.set_request_id.assert_called_once_with("req-123")

    def test_set_user_id(self, service):
        mock_cf = MagicMock()
        with patch.object(
                type(service._manager), 'context_filter',
                new_callable=PropertyMock,
                return_value=mock_cf
        ):
            service.set_user_id("user-42")
            mock_cf.set_user_id.assert_called_once_with("user-42")

    def test_request_context_manager(self, service):
        """request_context() يعمل كـ Context Manager"""
        mock_cf = MagicMock()
        mock_cf.request_context.return_value.__enter__ = MagicMock()
        mock_cf.request_context.return_value.__exit__ = MagicMock()

        with patch.object(
                type(service._manager), 'context_filter',
                new_callable=PropertyMock,
                return_value=mock_cf
        ):
            with service.request_context("req-123", user_id="user-42"):
                pass

            mock_cf.request_context.assert_called_once_with(
                request_id="req-123",
                correlation_id=None,
                user_id="user-42",
            )

    def test_request_context_without_filter(self, service):
        """request_context() يعمل حتى بدون ContextFilter"""
        with patch.object(
                type(service._manager), 'context_filter',
                new_callable=PropertyMock,
                return_value=None
        ):
            # يجب ألا يرفع خطأ
            with service.request_context("req-123"):
                pass


# ==========================================================
# 8. Health Check Tests
# ==========================================================

class TestHealthCheck:
    def test_health_check_when_ready(self, service):
        """health_check() يُرجع تقريراً كاملاً"""
        mock_manager_health = {
            "healthy": True,
            "health_score": 95,
            "status": "ready",
            "last_exception": None,
        }
        mock_metrics_health = {"healthy": True, "metric_count": 5}

        with patch.object(service._manager, 'health_check', return_value=mock_manager_health):
            with patch.object(service._metrics, 'health_check', return_value=mock_metrics_health):
                result = service.health_check()

                assert result["healthy"] is True
                assert result["health_score"] >= 70
                assert "logging" in result
                assert "metrics" in result

    def test_health_check_when_not_ready(self, service):
        """health_check() يُرجع healthy=False عند الفشل"""
        mock_manager_health = {
            "healthy": False,
            "status": "failed",
            "last_exception": "Something went wrong",
        }
        mock_metrics_health = {"healthy": True}

        with patch.object(service._manager, 'health_check', return_value=mock_manager_health):
            with patch.object(service._metrics, 'health_check', return_value=mock_metrics_health):
                result = service.health_check()

                assert result["healthy"] is False
                assert result["health_score"] < 70

    def test_health_score_calculation(self, service):
        """حساب Health Score"""
        # حالة مثالية
        mock_manager_health = {"healthy": True, "last_exception": None}
        mock_metrics_health = {"healthy": True}

        with patch.object(service._manager, 'health_check', return_value=mock_manager_health):
            with patch.object(service._metrics, 'health_check', return_value=mock_metrics_health):
                result = service.health_check()
                assert result["health_score"] == 100

    def test_health_score_with_exception(self, service):
        """Health Score ينخفض عند وجود exception"""
        mock_manager_health = {"healthy": True, "last_exception": "Error"}
        mock_metrics_health = {"healthy": True}

        with patch.object(service._manager, 'health_check', return_value=mock_manager_health):
            with patch.object(service._metrics, 'health_check', return_value=mock_metrics_health):
                result = service.health_check()
                assert result["health_score"] == 80  # 100 - 20


# ==========================================================
# 9. Metrics Tests
# ==========================================================

class TestMetrics:
    def test_get_metrics_includes_both(self, service):
        """get_metrics() يشمل Logging و Metrics"""
        mock_logging_metrics = {"version": "2.1.0", "status": "ready"}
        mock_metrics_metrics = {"version": "1.2.0", "metric_count": 5}

        with patch.object(service._manager, 'get_metrics', return_value=mock_logging_metrics):
            with patch.object(service._metrics, 'get_metrics', return_value=mock_metrics_metrics):
                result = service.get_metrics()

                assert result["version"] == SERVICE_VERSION
                assert "logging" in result
                assert "metrics" in result

    def test_metrics_property(self, service):
        """الوصول إلى MetricsService"""
        assert service.metrics is service._metrics


# ==========================================================
# 10. Uptime Tests
# ==========================================================

class TestUptime:
    def test_uptime_delegates_to_manager(self, service):
        with patch.object(
                type(service._manager), 'uptime_seconds',
                new_callable=PropertyMock,
                return_value=123.45
        ):
            assert service.uptime_seconds == 123.45


# ==========================================================
# 11. Metadata Tests
# ==========================================================

class TestMetadata:
    def test_version(self, service):
        assert service.version == SERVICE_VERSION

    def test_to_dict(self, service):
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            with patch.object(
                    type(service._manager), 'uptime_seconds',
                    new_callable=PropertyMock,
                    return_value=10.0
            ):
                with patch.object(service._manager, 'health_check',
                                  return_value={"healthy": True, "last_exception": None}):
                    with patch.object(service._metrics, 'health_check', return_value={"healthy": True}):
                        result = service.to_dict()

                        assert result["version"] == SERVICE_VERSION
                        assert result["is_ready"] is True

    def test_repr(self, service):
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            repr_str = repr(service)
            assert "ObservabilityService" in repr_str
            assert "ready" in repr_str


# ==========================================================
# 12. Error Handling Tests
# ==========================================================

class TestErrorHandling:
    def test_initialize_with_failing_manager(self, service, mock_config_service):
        """initialize() يتعامل مع فشل Manager"""
        with patch.object(service._manager, 'configure', side_effect=RuntimeError("Manager failed")):
            with pytest.raises(RuntimeError, match="Manager failed"):
                service.initialize(mock_config_service)

    def test_shutdown_with_failing_manager(self, service):
        """shutdown() يتعامل مع فشل Manager"""
        with patch.object(service._manager, 'shutdown', side_effect=RuntimeError("Shutdown failed")):
            with pytest.raises(RuntimeError, match="Shutdown failed"):
                service.shutdown()


# ==========================================================
# 13. Integration Tests (مع Mocks)
# ==========================================================

class TestIntegration:
    def test_full_lifecycle(self, service, mock_config_service):
        """سيناريو دورة حياة كاملة"""
        # 1. Initialize
        with patch.object(service._manager, 'configure') as mock_configure:
            mock_configure.return_value = {}
            with patch.object(service._metrics, 'freeze'):
                service.initialize(mock_config_service)

        # 2. Use
        with patch.object(
                type(service._manager), 'status',
                new_callable=PropertyMock,
                return_value=ManagerStatus.READY
        ):
            assert service.is_ready is True

        # 3. Health Check
        with patch.object(service._manager, 'health_check', return_value={"healthy": True, "last_exception": None}):
            with patch.object(service._metrics, 'health_check', return_value={"healthy": True}):
                health = service.health_check()
                assert health["healthy"] is True

        # 4. Shutdown
        with patch.object(service._manager, 'shutdown', return_value={"closed_handlers": 1}):
            with patch.object(service._metrics, 'unfreeze'):
                result = service.shutdown()
                assert result["closed_handlers"] == 1

    def test_reload_lifecycle(self, service, mock_config_service):
        """سيناريو إعادة التحميل"""
        with patch.object(service._manager, 'atomic_reload') as mock_reload:
            mock_reload.return_value = {"success": True, "swapped": True}
            with patch.object(service._metrics, 'unfreeze'):
                with patch.object(service._metrics, 'freeze'):
                    result = service.reload(mock_config_service)

            assert result["success"] is True
            assert result["swapped"] is True


# ==========================================================
# 14. All Specialized Loggers (تغطية 187-219)
# ==========================================================

class TestAllSpecializedLoggers:
    @pytest.mark.parametrize("prop", [
        "system", "error", "security", "ai", "audit",
        "performance", "database", "network", "cache", "config",
    ])
    def test_specialized_logger_property(self, service, prop):
        mock_logger = MagicMock()
        mock_factory = MagicMock(**{prop: mock_logger})
        with patch.object(service._manager, "_logger_factory", mock_factory, create=True):
            result = getattr(service, prop)
            assert result is mock_logger


# ==========================================================
# 15. Context Methods مع context_filter = None (تغطية 227->exit, 232->exit)
# ==========================================================

class TestContextMethodsNoFilter:
    def test_set_request_id_no_filter(self, service):
        with patch.object(type(service._manager), "context_filter",
                          new_callable=PropertyMock, return_value=None):
            assert service.set_request_id("req") is None

    def test_set_user_id_no_filter(self, service):
        with patch.object(type(service._manager), "context_filter",
                          new_callable=PropertyMock, return_value=None):
            assert service.set_user_id("user") is None

    def test_set_correlation_id_no_filter(self, service):
        with patch.object(type(service._manager), "context_filter",
                          new_callable=PropertyMock, return_value=None):
            assert service.set_correlation_id("corr") is None


# ==========================================================
# 16. to_dict عندما not ready (تغطية 304)
# ==========================================================

class TestToDictNotReady:
    def test_to_dict_when_not_ready(self, service):
        with patch.object(type(service._manager), "status",
                          new_callable=PropertyMock,
                          return_value=ManagerStatus.NOT_INITIALIZED):
            with patch.object(type(service._manager), "uptime_seconds",
                              new_callable=PropertyMock, return_value=0.0):
                result = service.to_dict()
                assert result["health"] is None
                assert result["is_ready"] is False


# ==========================================================
# 17. Health Score Edge Cases (تغطية فروع _calculate_overall_health_score)
# ==========================================================

class TestHealthScoreEdgeCases:
    def test_score_manager_not_healthy(self, service):
        score = service._calculate_overall_health_score(
            {"healthy": False, "last_exception": None},
            {"healthy": True},
        )
        assert score == 60  # 100 - 40

    def test_score_metrics_not_healthy(self, service):
        score = service._calculate_overall_health_score(
            {"healthy": True, "last_exception": None},
            {"healthy": False},
        )
        assert score == 80  # 100 - 20

    def test_score_all_bad(self, service):
        score = service._calculate_overall_health_score(
            {"healthy": False, "last_exception": "err"},
            {"healthy": False},
        )
        assert score == 20  # 100 - 40 - 20 - 20

    def test_score_never_negative(self, service):
        score = service._calculate_overall_health_score(
            {"healthy": False, "last_exception": "err"},
            {"healthy": False},
        )
        assert score >= 0