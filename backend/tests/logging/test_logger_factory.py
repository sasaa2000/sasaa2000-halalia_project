"""
اختبارات الوحدة لـ LoggerFactory — مطابقة للنسخة v1.4.1 الفعلية.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import pytest

from core.logging.logger_factory import (
    FACTORY_VERSION,
    LoggerFactory,
    LoggerName,
    LoggerRegistrationError,
    UnknownLoggerError,
)


@pytest.fixture(autouse=True)
def reset_factory():
    LoggerFactory.reset_instance()
    yield
    LoggerFactory.reset_instance()


@pytest.fixture
def factory():
    return LoggerFactory()


# ==========================================================
# 1. Singleton
# ==========================================================

class TestSingleton:
    def test_singleton(self):
        a = LoggerFactory()
        b = LoggerFactory()
        assert a is b

    def test_reset_instance_creates_new(self):
        a = LoggerFactory()
        LoggerFactory.reset_instance()
        b = LoggerFactory()
        assert a is not b


# ==========================================================
# 2. Get Logger
# ==========================================================

class TestGetLogger:
    def test_create_logger(self, factory):
        logger = factory.get_logger("api_create")
        assert logger.name == "api_create"

    def test_same_logger_returned(self, factory):
        a = factory.get_logger("api_same")
        b = factory.get_logger("api_same")
        assert a is b

    @pytest.mark.parametrize("level", [
        logging.DEBUG, logging.INFO, logging.WARNING,
        logging.ERROR, logging.CRITICAL,
    ])
    def test_log_level(self, factory, level):
        logger = factory.get_logger(f"api_level_{level}", level=level)
        assert logger.level == level

    @pytest.mark.parametrize("name", ["", "   ", None])
    def test_invalid_name(self, factory, name):
        with pytest.raises(ValueError):
            factory.get_logger(name)

    def test_register_external_logger_invalid_name(self, factory):
        logger = logging.getLogger("external_invalid_name")

        with pytest.raises(LoggerRegistrationError, match="non-empty"):
            factory.register_external_logger("", logger)

    def test_register_external_logger_invalid_logger(self, factory):
        with pytest.raises(
            LoggerRegistrationError,
            match="logging.Logger",
        ):
            factory.register_external_logger(
                "invalid_external",
                object(),
            )

# ==========================================================
# 3. Console Handler
# ==========================================================

class TestConsoleHandler:
    def test_console_handler_created(self, factory):
        logger = factory.get_logger_with_console("console_created")
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_console_handler_not_duplicated(self, factory):
        logger = factory.get_logger_with_console("console_dup")
        count_before = len(logger.handlers)
        factory.get_logger_with_console("console_dup")
        assert len(logger.handlers) == count_before


# ==========================================================
# 4. File Handler
# ==========================================================

class TestFileHandler:
    def test_file_handler_created(self, factory, tmp_path):
        logfile = tmp_path / "app.log"
        logger = factory.get_logger_with_file("file_created", str(logfile), level=logging.INFO)
        logger.info("hello")
        assert logfile.exists()
        assert "hello" in logfile.read_text()

    def test_file_handler_not_duplicated(self, factory, tmp_path):
        logfile = tmp_path / "app.log"
        logger = factory.get_logger_with_file("file_dup", str(logfile), level=logging.INFO)
        count_before = len(logger.handlers)
        factory.get_logger_with_file("file_dup", str(logfile), level=logging.INFO)
        assert len(logger.handlers) == count_before

    def test_file_handler_ignores_non_file_handler(self, factory, tmp_path):
        logfile = tmp_path / "app.log"
        logger = factory.get_logger("file_non_file_handler")

        logger.addHandler(logging.StreamHandler())

        result = factory.get_logger_with_file(
            "file_non_file_handler",
            logfile,
            level=logging.INFO,
        )

        assert result is logger
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_file_handler_adds_when_existing_file_handler_has_different_path(
            self, factory, tmp_path
        ):

        first_log = tmp_path / "first.log"
        second_log = tmp_path / "second.log"

        logger = factory.get_logger_with_file(
            "file_different_path",
            first_log,
            level=logging.INFO,
        )

        result = factory.get_logger_with_file(
            "file_different_path",
            second_log,
            level=logging.INFO,
        )

        assert result is logger

        file_paths = {
            Path(h.baseFilename).resolve()
            for h in logger.handlers
            if isinstance(h, logging.FileHandler)
        }

        assert first_log.resolve() in file_paths
        assert second_log.resolve() in file_paths


# ==========================================================
# 5. Exception Logging
# ==========================================================

class TestExceptionLogging:
    def test_exception_logging(self, factory, tmp_path):
        logfile = tmp_path / "exc.log"
        logger = factory.get_logger_with_file("exc_test", str(logfile), level=logging.DEBUG)
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            logger.exception("failure")
        text = logfile.read_text()
        assert "RuntimeError" in text
        assert "boom" in text



# ==========================================================
# 6. Thread Safety
# ==========================================================

class TestThreadSafety:
    def test_multithread_logging(self, factory, tmp_path):
        logfile = tmp_path / "threads.log"
        logger = factory.get_logger_with_file("thread_test", str(logfile), level=logging.INFO)

        def worker():
            for _ in range(100):
                logger.info("hello")

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        lines = logfile.read_text().splitlines()
        assert len(lines) == 1000


# ==========================================================
# 7. Lazy Initialization
# ==========================================================

class TestLazyInitialization:
    def test_logger_created_only_once(self, factory):
        assert "lazy_test" not in factory._metadata
        factory.get_logger("lazy_test")
        assert "lazy_test" in factory._metadata


# ==========================================================
# 8. Specialized Loggers
# ==========================================================

class TestSpecializedLoggers:

    def test_all_specialized_loggers(self, factory):
        result = factory.initialize_specialized_loggers()
        assert len(result) == len(LoggerName)
        assert len(factory.list_specialized_loggers()) == len(LoggerName)

    def test_specialized_propagate_false(self, factory):
        logger = factory.system
        assert logger.propagate is False

    def test_get_specialized_rejects_non_enum(self, factory):
        with pytest.raises(UnknownLoggerError):
            factory.get_specialized("NOT_A_LOGGER_NAME")


# ==========================================================
# 9. Freeze
# ==========================================================

class TestFreeze:
    def test_freeze_prevents_external_registration(self, factory):
        factory.freeze()
        with pytest.raises(LoggerRegistrationError, match="frozen"):
            factory.register_external_logger("ext_test", logging.getLogger("ext_test"))

    def test_unfreeze_allows_registration(self, factory):
        factory.freeze()
        factory.unfreeze()
        factory.register_external_logger("ext_test2", logging.getLogger("ext_test2"))

    def test_is_frozen_property(self, factory):
            assert factory.is_frozen is False

            factory.freeze()

            assert factory.is_frozen is True

            factory.unfreeze()

            assert factory.is_frozen is False


# ==========================================================
# 10. Metadata & Listing
# ==========================================================

class TestMetadataAndListing:
    def test_get_metadata(self, factory):
        factory.get_logger("meta_test")
        metadata = factory.get_metadata("meta_test")
        assert metadata["access_count"] >= 1

    def test_get_metadata_all(self, factory):
        factory.get_logger("meta_a")
        factory.get_logger("meta_b")
        all_metadata = factory.get_metadata()
        assert "meta_a" in all_metadata
        assert "meta_b" in all_metadata

    def test_get_metadata_unknown_raises(self, factory):
        from core.logging.logger_factory import UnknownLoggerError
        with pytest.raises(UnknownLoggerError):
            factory.get_metadata("nonexistent_logger")

    def test_list_loggers(self, factory):
        factory.get_logger("list_a")
        factory.get_logger("list_b")
        loggers = factory.list_loggers()
        assert "list_a" in loggers
        assert "list_b" in loggers

    def test_version(self, factory):
        assert FACTORY_VERSION == "1.4.1"


# ==========================================================
# 11. Unregister
# ==========================================================

class TestUnregister:
    def test_unregister_existing(self, factory):
        factory.get_logger("unreg_test")
        assert factory.unregister_logger("unreg_test") is True
        assert "unreg_test" not in factory.list_loggers()

    def test_unregister_nonexistent(self, factory):
        assert factory.unregister_logger("never_registered") is False

    def test_unregister_when_frozen_raises(self, factory):
        factory.get_logger("frozen_unreg")
        factory.freeze()
        with pytest.raises(LoggerRegistrationError, match="frozen"):
            factory.unregister_logger("frozen_unreg")

    def test_unregister_invalid_name(self, factory):
        with pytest.raises(
                ValueError,
                match="non-empty string",
        ):
            factory.unregister_logger("")

    def test_register_external_logger_as_specialized(self, factory):
        logger = logging.getLogger("external_specialized")

        result = factory.register_external_logger(
            "external_specialized",
            logger,
            is_specialized=True,
        )

        assert result is logger
        assert "external_specialized" in factory.list_specialized_loggers()


# ==========================================================
# 12. Specialized Properties
# ==========================================================

class TestSpecializedProperties:
    @pytest.mark.parametrize("prop", [
        "system", "error", "security", "ai", "audit",
        "performance", "database", "network", "cache", "config",
    ])
    def test_specialized_property_returns_logger(self, factory, prop):
        logger = getattr(factory, prop)
        assert isinstance(logger, logging.Logger)
        assert logger.propagate is False
        assert logger.name == getattr(LoggerName, prop.upper()).value


# ==========================================================
# 13. Cached get_logger
# ==========================================================

class TestCachedGetLogger:
    def test_cached_path_applies_level(self, factory):
        a = factory.get_logger("cached_level", level=logging.INFO)
        b = factory.get_logger("cached_level", level=logging.DEBUG)
        assert a is b
        assert b.level == logging.DEBUG

    def test_cached_path_sets_propagate(self, factory):
        a = factory.get_logger("cached_prop", propagate=False)
        b = factory.get_logger("cached_prop", propagate=True)
        assert a is b
        assert b.propagate is True


# ==========================================================
# 14. Color Formatter
# ==========================================================

class TestColorFormatter:
    def test_color_applied_for_known_level(self):
        from core.logging.logger_factory import _ColorFormatter
        formatter = _ColorFormatter(fmt="%(message)s")
        record = logging.LogRecord("t", logging.ERROR, "", 0, "msg", None, None)
        assert "\033[" in formatter.format(record)

    def test_no_color_for_unknown_level(self):
        from core.logging.logger_factory import _ColorFormatter
        formatter = _ColorFormatter(fmt="%(message)s")
        record = logging.LogRecord("t", logging.NOTSET, "", 0, "msg", None, None)
        assert "\033[" not in formatter.format(record)

    def test_console_with_colors_uses_color_formatter(self, factory):
        from core.logging.logger_factory import _ColorFormatter
        logger = factory.get_logger_with_console("color_console", level=logging.INFO, use_colors=True)
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, _ColorFormatter)


# ==========================================================
# 15. Module-level Functions
# ==========================================================

class TestModuleFunctions:
    def test_module_get_specialized(self):
        from core.logging.logger_factory import get_specialized
        logger = get_specialized(LoggerName.AI)
        assert logger.name == LoggerName.AI.value

    def test_module_initialize_specialized(self):
        from core.logging.logger_factory import initialize_specialized_loggers
        result = initialize_specialized_loggers()
        assert len(result) == len(LoggerName)

    def test_module_get_logger(self):
        from core.logging.logger_factory import get_logger
        logger = get_logger("module_level", level=logging.WARNING)
        assert logger.level == logging.WARNING