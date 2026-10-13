"""
اختبارات الوحدة لـ log_handlers.py
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

import pytest

from core.logging.log_handlers import (
    HANDLERS_VERSION,
    CacheKeyBuilder,
    HandlerFactory,
    HandlerRegistrationError,
    HandlerType,
    UnknownHandlerError,
    get_console_handler,
    get_null_handler,
)


@pytest.fixture(autouse=True)
def reset_factory():
    HandlerFactory._instance = None
    yield
    inst = HandlerFactory._instance
    if inst is not None:
        try:
            inst.close_all()
        except Exception:
            pass
    HandlerFactory._instance = None


# ==========================================================
# 1. CacheKeyBuilder
# ==========================================================

class TestCacheKeyBuilder:
    def test_normalize_none(self):
        assert CacheKeyBuilder.normalize(None) == "None"

    def test_normalize_bool(self):
        assert CacheKeyBuilder.normalize(True) == "bool:True"

    def test_normalize_num(self):
        assert CacheKeyBuilder.normalize(5) == "num:5"

    def test_normalize_str(self):
        assert CacheKeyBuilder.normalize("x") == "str:x"

    def test_normalize_path(self):
        assert CacheKeyBuilder.normalize(Path("a")).startswith("path:")

    def test_normalize_enum(self):
        from enum import Enum
        class PlainEnum(Enum):
            A = "a"
        assert CacheKeyBuilder.normalize(PlainEnum.A).startswith("enum:")

    def test_normalize_callable(self):
        def f():
            pass
        assert CacheKeyBuilder.normalize(f).startswith("obj:")

    def test_build_deterministic(self):
        a = CacheKeyBuilder.build("file", {"b": 1, "a": 2})
        b = CacheKeyBuilder.build("file", {"a": 2, "b": 1})
        assert a == b


# ==========================================================
# 2. HandlerFactory.create
# ==========================================================

class TestHandlerFactoryCreate:
    def test_create_console(self):
        assert isinstance(HandlerFactory().create(HandlerType.CONSOLE), logging.StreamHandler)

    def test_create_file(self, tmp_path):
        h = HandlerFactory().create(HandlerType.FILE, filename="t.log", log_dir=tmp_path)
        assert isinstance(h, logging.FileHandler)

    def test_create_rotating(self, tmp_path):
        h = HandlerFactory().create(HandlerType.ROTATING_FILE, filename="t.log", log_dir=tmp_path)
        assert isinstance(h, RotatingFileHandler)

    def test_create_timed(self, tmp_path):
        h = HandlerFactory().create(HandlerType.TIMED_ROTATING, filename="t.log", log_dir=tmp_path)
        assert isinstance(h, TimedRotatingFileHandler)

    def test_create_null(self):
        assert isinstance(HandlerFactory().create(HandlerType.NULL), logging.NullHandler)

    def test_file_cached(self, tmp_path):
        f = HandlerFactory()
        a = f.create(HandlerType.FILE, filename="c.log", log_dir=tmp_path, delay=False)
        b = f.create(HandlerType.FILE, filename="c.log", log_dir=tmp_path, delay=False)
        assert a is b
        assert f.cache_hits == 1

    def test_console_not_cached(self):
        f = HandlerFactory()
        a = f.create(HandlerType.CONSOLE)
        b = f.create(HandlerType.CONSOLE)
        assert a is not b


# ==========================================================
# 3. create_from_string
# ==========================================================

class TestCreateFromString:
    def test_valid(self):
        assert isinstance(HandlerFactory().create_from_string("console"), logging.StreamHandler)

    def test_invalid_production_raises(self):
        with pytest.raises(UnknownHandlerError):
            HandlerFactory().create_from_string("nope", environment="production")

    def test_invalid_dev_warns(self):
        with pytest.warns(UserWarning):
            h = HandlerFactory().create_from_string("nope", environment="development")
        assert isinstance(h, logging.StreamHandler)


# ==========================================================
# 4. Registration
# ==========================================================

class TestRegistration:
    def test_register_and_supported(self):
        f = HandlerFactory()
        f.register_handler("custom", lambda: logging.NullHandler())
        assert "custom" in f.supported_handlers()

    def test_register_reserved_raises(self):
        with pytest.raises(HandlerRegistrationError):
            HandlerFactory().register_handler("console", lambda: logging.NullHandler())

    def test_register_frozen_raises(self):
        f = HandlerFactory()
        f.freeze()
        with pytest.raises(RuntimeError):
            f.register_handler("x", lambda: logging.NullHandler())

    def test_register_empty_raises(self):
        with pytest.raises(ValueError):
            HandlerFactory().register_handler("", lambda: logging.NullHandler())

    def test_register_non_callable_raises(self):
        with pytest.raises(TypeError):
            HandlerFactory().register_handler("x", "nope")

    def test_unregister(self):
        f = HandlerFactory()
        f.register_handler("custom", lambda: logging.NullHandler())
        assert f.unregister_handler("custom") is True
        assert f.unregister_handler("custom") is False


# ==========================================================
# 5. Resource Management
# ==========================================================

class TestClose:
    def test_close_all(self, tmp_path):
        f = HandlerFactory()
        f.create(HandlerType.FILE, filename="x.log", log_dir=tmp_path)
        assert f.close_all() >= 1
        assert f.cache_size == 0

    def test_close_handler(self, tmp_path):
        f = HandlerFactory()
        h = f.create(HandlerType.FILE, filename="y.log", log_dir=tmp_path)
        f.close_handler(h)
        assert f.cache_size == 0

    def test_shutdown(self, tmp_path):
        f = HandlerFactory()
        f.create(HandlerType.FILE, filename="z.log", log_dir=tmp_path)
        assert f.shutdown() >= 1

    def test_clear_cache_frozen_raises(self):
        f = HandlerFactory()
        f.freeze()
        with pytest.raises(RuntimeError):
            f.clear_cache()

    def test_clear_registry_frozen_raises(self):
        f = HandlerFactory()
        f.freeze()
        with pytest.raises(RuntimeError):
            f.clear_registry()


# ==========================================================
# 6. Metrics & Metadata
# ==========================================================

class TestMetrics:
    def test_get_metrics(self):
        assert HandlerFactory().get_metrics()["version"] == HANDLERS_VERSION

    def test_repr(self):
        assert "HandlerFactory" in repr(HandlerFactory())


# ==========================================================
# 7. Convenience Functions
# ==========================================================

class TestConvenience:
    def test_get_console_handler(self):
        assert isinstance(get_console_handler(), logging.StreamHandler)

    def test_get_null_handler(self):
        assert isinstance(get_null_handler(), logging.NullHandler)

def test_cache_key_builder_normalize_object_with_class_name():
    class CustomObject:
        pass

    value = CustomObject()
    result = CacheKeyBuilder.normalize(value)

    assert result.startswith("obj:")


def test_handler_factory_singleton_reuses_instance():
    first = HandlerFactory()
    second = HandlerFactory()

    assert first is second


def test_handler_factory_init_is_idempotent():
    factory = HandlerFactory()

    factory.__init__()

    assert factory.is_initialized is True


def test_close_handler_invalidates_cached_handler(tmp_path):
    factory = HandlerFactory()

    handler = factory.create(
        HandlerType.FILE,
        filename="close-test.log",
        log_dir=tmp_path,
    )

    factory.close_handler(handler)

    assert factory.cache_size == 0


def test_is_handler_valid_returns_false_for_closed_stream():
    factory = HandlerFactory()

    class FakeHandler:
        stream = None
        lock = object()

    assert factory._is_handler_valid(FakeHandler()) is False


def test_is_handler_valid_returns_false_for_closed_lock():
    factory = HandlerFactory()

    class FakeHandler:
        stream = object()
        lock = None

    assert factory._is_handler_valid(FakeHandler()) is False


def test_is_handler_valid_handles_exception():
    factory = HandlerFactory()

    class BrokenHandler:
        @property
        def stream(self):
            raise RuntimeError("broken")

    assert factory._is_handler_valid(BrokenHandler()) is False