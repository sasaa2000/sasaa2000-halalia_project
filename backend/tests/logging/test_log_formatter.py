"""
اختبارات الوحدة لـ log_formatter.py
"""

from __future__ import annotations

import json
import logging
import sys

import pytest

from core.logging.log_formatter import (
    FORMATTER_VERSION,
    AnsiColor,
    ConsoleFormatter,
    DetailedFormatter,
    FormatterFactory,
    FormatterType,
    JsonFormatter,
    MinimalFormatter,
    RawFormatter,
    SystemMetadata,
    TimestampUtil,
    UnknownFormatterError,
    get_console_formatter,
    get_json_formatter,
)


# ==========================================================
# Fixtures & Helpers
# ==========================================================

@pytest.fixture(autouse=True)
def reset_factory():
    FormatterFactory._instance = None
    yield
    FormatterFactory._instance = None


def make_record(msg="test message", level=logging.INFO, exc_info=None, **extra):
    record = logging.LogRecord(
        name="test.logger", level=level, pathname="test.py",
        lineno=42, msg=msg, args=None, exc_info=exc_info,
    )
    record.module = "test"
    record.funcName = "test_func"
    for k, v in extra.items():
        setattr(record, k, v)
    return record


# ==========================================================
# 1. ConsoleFormatter
# ==========================================================

class TestConsoleFormatter:
    def test_format_basic_no_colors(self):
        f = ConsoleFormatter(use_colors=False)
        output = f.format(make_record("hello"))
        assert "hello" in output
        assert "test.logger" in output

    def test_format_with_colors(self):
        f = ConsoleFormatter(use_colors=True)
        output = f.format(make_record("hello", level=logging.ERROR))
        assert "hello" in output
        assert "\033[" in output

    def test_format_with_thread(self):
        f = ConsoleFormatter(use_colors=False, show_thread=True)
        output = f.format(make_record("hello"))
        assert "[" in output

    def test_format_with_module(self):
        f = ConsoleFormatter(use_colors=False, show_module=True)
        output = f.format(make_record("hello"))
        assert "test:42" in output

    def test_format_with_exception(self):
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
        f = ConsoleFormatter(use_colors=False)
        output = f.format(make_record("err", exc_info=exc_info))
        assert "ValueError" in output
        assert "boom" in output


# ==========================================================
# 2. JsonFormatter
# ==========================================================

class TestJsonFormatter:
    def test_format_valid_json(self):
        f = JsonFormatter()
        data = json.loads(f.format(make_record("hello")))
        assert data["message"] == "hello"
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"

    def test_json_includes_system_metadata(self):
        data = json.loads(JsonFormatter().format(make_record("hello")))
        assert "hostname" in data
        assert data["application"] == "HALALIA"

    def test_json_with_context(self):
        f = JsonFormatter(include_context=True)
        record = make_record("hello", environment="production", request_id="req-1")
        data = json.loads(f.format(record))
        assert data["metadata"]["environment"] == "production"
        assert data["metadata"]["request_id"] == "req-1"

    def test_json_without_context(self):
        f = JsonFormatter(include_context=False)
        data = json.loads(f.format(make_record("hello")))
        assert "metadata" not in data

    def test_json_with_source(self):
        f = JsonFormatter(include_source=True)
        data = json.loads(f.format(make_record("hello")))
        assert data["source"]["module"] == "test"
        assert data["source"]["line"] == 42

    def test_json_without_source(self):
        f = JsonFormatter(include_source=False)
        data = json.loads(f.format(make_record("hello")))
        assert "source" not in data

    def test_json_with_exception(self):
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            exc_info = sys.exc_info()
        f = JsonFormatter()
        data = json.loads(f.format(make_record("err", exc_info=exc_info)))
        assert data["exception"]["type"] == "RuntimeError"
        assert data["exception"]["message"] == "boom"

    def test_json_with_extra_data(self):
        f = JsonFormatter()
        record = make_record("hello", extra_data={"user": "admin"})
        data = json.loads(f.format(record))
        assert data["data"]["user"] == "admin"


# ==========================================================
# 3. Minimal & Raw Formatters
# ==========================================================

class TestMinimalRawFormatters:
    def test_minimal_formatter(self):
        assert MinimalFormatter().format(make_record("hello")) == "hello"

    def test_raw_formatter(self):
        assert RawFormatter().format(make_record("hello")) == "hello"


# ==========================================================
# 4. DetailedFormatter
# ==========================================================

class TestDetailedFormatter:
    def test_detailed_contains_fields(self):
        f = DetailedFormatter()
        output = f.format(make_record("hello"))
        assert "hello" in output
        assert "test.logger" in output
        assert "PID=" in output
        assert "test:42" in output

    def test_detailed_with_exception(self):
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
        f = DetailedFormatter()
        output = f.format(make_record("err", exc_info=exc_info))
        assert "ValueError" in output


# ==========================================================
# 5. TimestampUtil & SystemMetadata
# ==========================================================

class TestUtilities:
    def test_utc_iso(self):
        result = TimestampUtil.utc_iso(make_record())
        assert "T" in result

    def test_utc_formatted(self):
        result = TimestampUtil.utc_formatted(make_record(), "%Y-%m-%d")
        assert len(result) == 10

    def test_system_metadata_cached(self):
        a = SystemMetadata.get()
        b = SystemMetadata.get()
        assert a is b
        assert "hostname" in a
        assert a["application"] == "HALALIA"


# ==========================================================
# 6. FormatterFactory
# ==========================================================

class TestFormatterFactory:
    def test_create_console(self):
        assert isinstance(FormatterFactory().create(FormatterType.CONSOLE), ConsoleFormatter)

    def test_create_json(self):
        assert isinstance(FormatterFactory().create(FormatterType.JSON), JsonFormatter)

    def test_create_minimal(self):
        assert isinstance(FormatterFactory().create(FormatterType.MINIMAL), MinimalFormatter)

    def test_create_detailed(self):
        assert isinstance(FormatterFactory().create(FormatterType.DETAILED), DetailedFormatter)

    def test_create_raw(self):
        assert isinstance(FormatterFactory().create(FormatterType.RAW), RawFormatter)

    def test_create_caches_same_kwargs(self):
        factory = FormatterFactory()
        a = factory.create(FormatterType.CONSOLE, use_colors=False)
        b = factory.create(FormatterType.CONSOLE, use_colors=False)
        assert a is b

    def test_create_different_kwargs_different(self):
        factory = FormatterFactory()
        a = factory.create(FormatterType.CONSOLE, use_colors=True)
        b = factory.create(FormatterType.CONSOLE, use_colors=False)
        assert a is not b

    def test_create_from_string_valid(self):
        assert isinstance(FormatterFactory().create_from_string("json"), JsonFormatter)

    def test_create_from_string_invalid_fallback_console(self):
        assert isinstance(FormatterFactory().create_from_string("nonexistent"), ConsoleFormatter)


# ==========================================================
# 7. Dynamic Registration & Freeze
# ==========================================================

class TestRegistrationAndFreeze:
    def test_register_formatter_and_create(self):
        factory = FormatterFactory()
        factory.register_formatter("custom", lambda: MinimalFormatter())
        assert isinstance(factory.create_from_string("custom"), MinimalFormatter)

    def test_register_after_freeze_raises(self):
        factory = FormatterFactory()
        factory.freeze()
        with pytest.raises(RuntimeError, match="frozen"):
            factory.register_formatter("late", lambda: MinimalFormatter())

    def test_supported_formatters(self):
        supported = FormatterFactory().supported_formatters()
        assert "console" in supported
        assert "json" in supported

    def test_freeze_is_frozen(self):
        factory = FormatterFactory()
        assert factory.is_frozen is False
        factory.freeze()
        assert factory.is_frozen is True


# ==========================================================
# 8. Cache & Metrics & Metadata
# ==========================================================

class TestCacheAndMetrics:
    def test_clear_cache(self):
        factory = FormatterFactory()
        factory.create(FormatterType.CONSOLE)
        assert factory.cache_size >= 1
        count = factory.clear_cache()
        assert count >= 1
        assert factory.cache_size == 0

    def test_get_metrics(self):
        factory = FormatterFactory()
        factory.create(FormatterType.CONSOLE)
        m = factory.get_metrics()
        assert m["version"] == FORMATTER_VERSION
        assert m["creation_count"] >= 1

    def test_repr(self):
        assert "FormatterFactory" in repr(FormatterFactory())

    def test_version_property(self):
        assert FormatterFactory().version == FORMATTER_VERSION


# ==========================================================
# 9. Exceptions & Convenience
# ==========================================================

class TestExceptionsAndConvenience:
    def test_unknown_formatter_error(self):
        err = UnknownFormatterError("bad", ("console", "json"))
        assert "bad" in str(err)
        assert err.formatter_name == "bad"

    def test_get_console_formatter(self):
        assert isinstance(get_console_formatter(), ConsoleFormatter)

    def test_get_json_formatter(self):
        assert isinstance(get_json_formatter(), JsonFormatter)