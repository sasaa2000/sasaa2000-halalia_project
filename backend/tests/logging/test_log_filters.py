"""
Ø§Ø®ØªØ¨Ø§Ø±Ø§Øª Ø§Ù„ÙˆØ­Ø¯Ø© Ù„Ù€ log_filters.py
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

from core.logging.log_filters import (
    get_context_filter,
    get_level_filter,
    get_module_filter,
    get_message_pattern_filter,
    get_rate_limit_filter,
    FILTERS_VERSION,
    ContextFilter,
    FilterFactory,
    FilterRegistrationError,
    FilterType,
    LevelFilter,
    MaskingStrategies,
    MaskingStrategy,
    MessagePatternFilter,
    ModuleFilter,
    NullFilter,
    RateLimitFilter,
    SensitiveDataFilter,
    UnknownFilterError,
    _freeze,
    get_null_filter,
    get_sensitive_data_filter,
)


@pytest.fixture(autouse=True)
def reset_factory():
    FilterFactory._instance = None
    yield
    FilterFactory._instance = None


def make_record(msg="test message", level=logging.INFO, **extra):
    record = logging.LogRecord(
        name="test.logger", level=level, pathname="test.py",
        lineno=42, msg=msg, args=None, exc_info=None,
    )
    record.module = "test"
    record.funcName = "test_func"
    for k, v in extra.items():
        setattr(record, k, v)
    return record


# ==========================================================
# 1. _freeze (Cache Key Normalization)
# ==========================================================

class TestFreeze:
    def test_none(self):
        assert _freeze(None) is None

    def test_bool(self):
        assert _freeze(True) is True

    def test_numbers_and_str(self):
        assert _freeze(5) == 5
        assert _freeze(1.5) == 1.5
        assert _freeze("x") == "x"

    def test_enum(self):
        assert _freeze(FilterType.CONTEXT) == "context"

    def test_pattern(self):
        p = re.compile(r"abc")
        assert _freeze(p) == f"regex:abc:{p.flags}"

    def test_path(self):
        assert _freeze(Path("x")).startswith("path:")

    def test_dict_sorted(self):
        assert _freeze({"b": 1, "a": 2}) == (("a", 2), ("b", 1))

    def test_list_and_tuple(self):
        assert _freeze([1, 2]) == (1, 2)
        assert _freeze((1, 2)) == (1, 2)

    def test_set_sorted(self):
        assert _freeze({2, 1}) == (1, 2)

    def test_callable(self):
        def f():
            pass
        assert _freeze(f).startswith("callable:")

    def test_fallback_repr(self):
        class O:
            pass
        assert _freeze(O()).startswith("repr:")


# ==========================================================
# 2. MaskingStrategies
# ==========================================================

class TestMaskingStrategies:
    def test_redact(self):
        assert MaskingStrategies.redact("secret") == "***REDACTED***"

    def test_partial_short(self):
        assert MaskingStrategies.partial("abc") == "ab***"

    def test_partial_long(self):
        assert MaskingStrategies.partial("abcdefghij") == "abcd...hij"

    def test_hash(self):
        assert MaskingStrategies.hash("x").startswith("hash:")

    def test_remove(self):
        assert MaskingStrategies.remove("x") == "<removed>"

    def test_apply(self):
        assert MaskingStrategies.apply(MaskingStrategy.REDACT, "x") == "***REDACTED***"


# ==========================================================
# 3. SensitiveDataFilter
# ==========================================================

class TestSensitiveDataFilter:
    def test_mask_api_key_in_text(self):
        f = SensitiveDataFilter()
        record = make_record("api_key=ABCDEFGHIJKLMNOPQRSTUVWX123")
        f.filter(record)
        assert "ABCDEFGHIJKLMNOPQRSTUVWX123" not in record.msg
        assert "***REDACTED***" in record.msg

    def test_mask_password_in_text(self):
        f = SensitiveDataFilter()
        record = make_record("password=hunter2secretvalue")
        f.filter(record)
        assert "hunter2secretvalue" not in record.msg

    def test_mask_dict_sensitive_key(self):
        f = SensitiveDataFilter()
        record = make_record("data")
        record.extra_data = {"token": "abcdef123456", "user": "admin"}
        f.filter(record)
        assert record.extra_data["token"] == "***REDACTED***"
        assert record.extra_data["user"] == "admin"

    def test_mask_count(self):
        f = SensitiveDataFilter()
        f.filter(make_record("api_key=ABCDEFGHIJKLMNOPQRSTUVWX123"))
        assert f.mask_count >= 1

    def test_partial_strategy(self):
        f = SensitiveDataFilter(masking_strategy=MaskingStrategy.PARTIAL)
        record = make_record("data")
        record.extra_data = {"token": "abcdefghijklmnop"}
        f.filter(record)
        assert "..." in record.extra_data["token"]

    def test_include_pii_masks_email(self):
        f = SensitiveDataFilter(include_pii=True)
        record = make_record("contact user@example.com now")
        f.filter(record)
        assert "user@example.com" not in record.msg


# ==========================================================
# 4. ContextFilter
# ==========================================================

class TestContextFilter:
    def test_filter_adds_attrs(self):
        f = ContextFilter(environment="production")
        record = make_record("hello")
        f.filter(record)
        assert record.environment == "production"
        assert record.application == "HALALIA"

    def test_set_get_request_id(self):
        f = ContextFilter()
        token = f.set_request_id("req-1")
        assert f.get_request_id() == "req-1"
        f.reset_request_id(token)
        assert f.get_request_id() == "-"

    def test_request_context_manager(self):
        f = ContextFilter()
        with f.request_context("req-2", correlation_id="corr-1", user_id="u1"):
            assert f.get_request_id() == "req-2"
            assert f.get_correlation_id() == "corr-1"
            assert f.get_user_id() == "u1"
        assert f.get_request_id() == "-"


# ==========================================================
# 5. LevelFilter
# ==========================================================

class TestLevelFilter:
    def test_min_level(self):
        f = LevelFilter(min_level=logging.WARNING)
        assert f.filter(make_record("x", level=logging.INFO)) is False
        assert f.filter(make_record("x", level=logging.ERROR)) is True

    def test_max_level(self):
        f = LevelFilter(max_level=logging.WARNING)
        assert f.filter(make_record("x", level=logging.ERROR)) is False

    def test_exclude_levels(self):
        f = LevelFilter(exclude_levels=(logging.INFO,))
        assert f.filter(make_record("x", level=logging.INFO)) is False


# ==========================================================
# 6. ModuleFilter
# ==========================================================

class TestModuleFilter:
    def test_include(self):
        f = ModuleFilter(include_patterns=("test*",))
        assert f.filter(make_record("x")) is True

    def test_exclude(self):
        f = ModuleFilter(exclude_patterns=("test*",))
        assert f.filter(make_record("x")) is False

    def test_exact_mode(self):
        f = ModuleFilter(include_patterns=("test",), match_mode="exact")
        assert f.filter(make_record("x")) is True

    def test_substring_mode(self):
        f = ModuleFilter(include_patterns=("est",), match_mode="substring")
        assert f.filter(make_record("x")) is True


# ==========================================================
# 7. MessagePatternFilter
# ==========================================================

class TestMessagePatternFilter:
    def test_include(self):
        f = MessagePatternFilter(include_patterns=(r"error",))
        assert f.filter(make_record("an error occurred")) is True
        assert f.filter(make_record("all good")) is False

    def test_exclude(self):
        f = MessagePatternFilter(exclude_patterns=(r"secret",))
        assert f.filter(make_record("has secret")) is False

    def test_ignore_case(self):
        f = MessagePatternFilter(include_patterns=(r"ERROR",), ignore_case=True)
        assert f.filter(make_record("an error")) is True


# ==========================================================
# 8. RateLimitFilter
# ==========================================================

class TestRateLimitFilter:
    def test_allows_within_limit(self):
        f = RateLimitFilter(max_calls=5, window_seconds=60)
        assert all(f.filter(make_record("x")) for _ in range(5))

    def test_drops_over_limit(self):
        f = RateLimitFilter(max_calls=2, window_seconds=60)
        f.filter(make_record("x"))
        f.filter(make_record("x"))
        assert f.filter(make_record("x")) is False
        assert f.dropped_count == 1

    def test_reset(self):
        f = RateLimitFilter(max_calls=1, window_seconds=60)
        f.filter(make_record("x"))
        f.reset()
        assert f.bucket_count == 0


# ==========================================================
# 9. NullFilter
# ==========================================================

class TestNullFilter:
    def test_null_filter(self):
        assert NullFilter().filter(make_record("x")) is True


# ==========================================================
# 10. FilterFactory
# ==========================================================

class TestFilterFactory:
    def test_create_each_type(self):
        factory = FilterFactory()
        assert isinstance(factory.create(FilterType.SENSITIVE_DATA), SensitiveDataFilter)
        assert isinstance(factory.create(FilterType.CONTEXT), ContextFilter)
        assert isinstance(factory.create(FilterType.LEVEL), LevelFilter)
        assert isinstance(factory.create(FilterType.MODULE), ModuleFilter)
        assert isinstance(factory.create(FilterType.MESSAGE_PATTERN), MessagePatternFilter)
        assert isinstance(factory.create(FilterType.RATE_LIMIT), RateLimitFilter)
        assert isinstance(factory.create(FilterType.NULL), NullFilter)

    def test_caching_for_cacheable(self):
        factory = FilterFactory()
        a = factory.create(FilterType.RATE_LIMIT, max_calls=5)
        b = factory.create(FilterType.RATE_LIMIT, max_calls=5)
        assert a is b
        assert factory.cache_hits == 1

    def test_no_cache_for_non_cacheable(self):
        factory = FilterFactory()
        a = factory.create(FilterType.CONTEXT)
        b = factory.create(FilterType.CONTEXT)
        assert a is not b

    def test_create_from_string_valid(self):
        assert isinstance(FilterFactory().create_from_string("level"), LevelFilter)

    def test_create_from_string_invalid_production_raises(self):
        with pytest.raises(UnknownFilterError):
            FilterFactory().create_from_string("nope", environment="production")

    def test_create_from_string_invalid_dev_warns(self):
        with pytest.warns(UserWarning):
            f = FilterFactory().create_from_string("nope", environment="development")
        assert isinstance(f, NullFilter)

    def test_register_filter(self):
        factory = FilterFactory()
        factory.register_filter("custom", lambda: NullFilter())
        assert "custom" in factory.supported_filters()

    def test_register_reserved_raises(self):
        with pytest.raises(FilterRegistrationError):
            FilterFactory().register_filter("level", lambda: NullFilter())

    def test_register_frozen_raises(self):
        factory = FilterFactory()
        factory.freeze()
        with pytest.raises(RuntimeError):
            factory.register_filter("x", lambda: NullFilter())

    def test_register_empty_name_raises(self):
        with pytest.raises(ValueError):
            FilterFactory().register_filter("", lambda: NullFilter())

    def test_register_non_callable_raises(self):
        with pytest.raises(TypeError):
            FilterFactory().register_filter("x", "not_callable")

    def test_unregister(self):
        factory = FilterFactory()
        factory.register_filter("custom", lambda: NullFilter())
        assert factory.unregister_filter("custom") is True
        assert factory.unregister_filter("custom") is False

    def test_clear_cache_frozen_raises(self):
        factory = FilterFactory()
        factory.freeze()
        with pytest.raises(RuntimeError):
            factory.clear_cache()

    def test_get_metrics(self):
        factory = FilterFactory()
        factory.create(FilterType.RATE_LIMIT)
        assert factory.get_metrics()["version"] == FILTERS_VERSION

    def test_repr(self):
        assert "FilterFactory" in repr(FilterFactory())


# ==========================================================
# 11. Convenience Functions
# ==========================================================

class TestConvenience:
    def test_get_sensitive_data_filter(self):
             assert isinstance(get_sensitive_data_filter(), SensitiveDataFilter)

    def test_get_null_filter(self):
              assert isinstance(get_null_filter(), NullFilter) 


class TestAdditionalFilterCoverage:
    def test_partial_strategy_converts_non_string(self):
        assert MaskingStrategies.partial(123456789) == "1234...789"

    def test_sensitive_filter_sanitizes_tuple_dict_args(self):
        fltr = SensitiveDataFilter()
        record = make_record("user=%s", args=({"password": "secret"},))

        assert fltr.filter(record) is True
        assert record.args[0]["password"] != "secret"

    def test_sensitive_filter_sanitizes_nested_and_plain_values(self):
        fltr = SensitiveDataFilter()
        record = make_record("normal message")
        record.extra_data = {
            "nested": {"password": "secret"},
            "count": 42,
        }

        assert fltr.filter(record) is True
        assert record.extra_data["nested"]["password"] != "secret"
        assert record.extra_data["count"] == 42

    def test_context_request_context_with_optional_ids(self):
        fltr = ContextFilter()

        with fltr.request_context(
            request_id="req-1",
            correlation_id="corr-1",
            user_id="user-1",
        ):
            assert fltr.get_request_id() == "req-1"

        assert fltr.get_request_id() == "-"

    def test_module_filter_excludes_matching_module(self):
        fltr = ModuleFilter(exclude_patterns=("test*",))
        record = make_record("hello")
        record.name = "app"
        record.module = "test_module"

        assert fltr.filter(record) is False

    def test_module_filter_unknown_match_mode(self):
        fltr = ModuleFilter(include_patterns=("app",), match_mode="unknown")
        record = make_record("hello")
        record.name = "app"
        record.module = "main"

        assert fltr.filter(record) is False

    def test_message_pattern_filter_excludes_matching_message(self):
        fltr = MessagePatternFilter(exclude_patterns=("secret",))
        record = make_record("this contains secret data")

        assert fltr.filter(record) is False

    def test_rate_limit_global_bucket_and_counters(self):
        fltr = RateLimitFilter(max_calls=1, per_logger=False)
        first = make_record("first")
        second = make_record("second")
        first.name = "logger_a"
        second.name = "logger_b"

        assert fltr.filter(first) is True
        assert fltr.filter(second) is False
        assert fltr.allowed_count == 1
        assert fltr.dropped_count == 1
        assert fltr.bucket_count == 1

    def test_rate_limit_reset_missing_bucket(self):
        fltr = RateLimitFilter()
        fltr.reset("nonexistent_logger")
        assert fltr.bucket_count == 0

    def test_factory_custom_filter_and_management(self):
        factory = FilterFactory()
        factory.unfreeze()
        factory.register_filter("custom_coverage", lambda **kwargs: NullFilter())
        assert isinstance(
            factory.create_from_string("custom_coverage"),
            NullFilter,
        )
        assert factory.unregister_filter("custom_coverage") is True
        assert factory.clear_registry() >= 0

    def test_factory_convenience_functions(self):
        assert isinstance(get_context_filter(), ContextFilter)
        assert isinstance(get_level_filter(), LevelFilter)
        assert isinstance(get_module_filter(), ModuleFilter)
        assert isinstance(get_message_pattern_filter(), MessagePatternFilter)
        assert isinstance(get_rate_limit_filter(), RateLimitFilter)






