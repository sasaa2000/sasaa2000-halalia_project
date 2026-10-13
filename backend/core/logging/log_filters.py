"""
HALALIA Log Filters
Production Version 1.2.0 — VERIFIED (Final)

المؤسس:
    جمال الدين زيدان

الوصف:
    نظام ترشيح السجلات (Log Filtering) متعدد الأنماط.
    يوفر Factory لإنشاء وإدارة جميع أنواع الـ Filters.

التحسينات النهائية المطبقة (v1.2.0 — دمج الجزء 2):
    ✅ _freeze() — تطبيع موحد لجميع أنواع kwargs
    ✅ Cache Key Deterministic (لا يعتمد على id() أو set غير مرتب)
    ✅ دعم الأنواع المتداخلة (dict داخل list داخل tuple)
    ✅ دعم Path, Pattern, Enum, callable, set, frozenset
    ✅ جميع تحسينات v1.1.0 (contextvars, TTL, Strategy Pattern, etc.)
"""

from __future__ import annotations

import contextvars
import fnmatch
import hashlib
import logging
import os
import re
import socket
import threading
import time
import warnings
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

# ==========================================================
# 1. Constants
# ==========================================================

FILTERS_VERSION = "1.2.0"

DEFAULT_RATE_LIMIT_WINDOW = 60.0
DEFAULT_RATE_LIMIT_MAX_CALLS = 100
DEFAULT_RATE_LIMIT_TTL = 3600.0

# ==========================================================
# 2. Type Aliases
# ==========================================================

FilterFactoryCallable = Callable[..., logging.Filter]


# ==========================================================
# 3. Enums
# ==========================================================

class FilterType(str, Enum):
    SENSITIVE_DATA = "sensitive_data"
    CONTEXT = "context"
    LEVEL = "level"
    MODULE = "module"
    MESSAGE_PATTERN = "message_pattern"
    RATE_LIMIT = "rate_limit"
    NULL = "null"


class MaskingStrategy(str, Enum):
    REDACT = "redact"
    PARTIAL = "partial"
    HASH = "hash"
    REMOVE = "remove"


# ==========================================================
# 4. Exceptions
# ==========================================================

class UnknownFilterError(ValueError):
    def __init__(self, filter_name: str, available: Tuple[str, ...] = ()):
        self.filter_name = filter_name
        self.available = available
        sorted_available = tuple(sorted(available))
        super().__init__(
            f"Unknown filter type: '{filter_name}'. "
            f"Available: {sorted_available}"
        )


class FilterRegistrationError(ValueError):
    def __init__(self, name: str, reserved: Tuple[str, ...]):
        self.name = name
        self.reserved = reserved
        super().__init__(
            f"Cannot register filter '{name}': "
            f"name conflicts with built-in filter. "
            f"Reserved names: {tuple(sorted(reserved))}"
        )


# ==========================================================
# 5. Pattern Groups
# ==========================================================

DEFAULT_SECRET_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})'),
    re.compile(r'(?i)(token|bearer)\s*[=:]\s*["\']?([A-Za-z0-9_\-\.]{20,})'),
    re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']+)'),
    re.compile(r'(?i)(secret)\s*[=:]\s*["\']?([^\s"\']+)'),
    re.compile(r'(?i)(private[_-]?key)\s*[=:]\s*["\']?([^\s"\']+)'),
)

DEFAULT_PII_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
)

DEFAULT_SENSITIVE_KEYS: Tuple[str, ...] = (
    "token", "password", "secret", "pin", "api_key", "apikey",
    "authorization", "cookie", "session_id", "credit_card",
    "private_key", "access_token", "refresh_token"
)


# ==========================================================
# 6. Masking Strategies (Strategy Pattern)
# ==========================================================

class MaskingStrategies:
    __slots__ = ()

    @staticmethod
    def redact(value: Any, redaction_text: str = "***REDACTED***") -> str:
        return redaction_text

    @staticmethod
    def partial(value: Any, **kwargs) -> str:
        if not isinstance(value, str):
            value = str(value)
        if len(value) <= 8:
            return value[:2] + "***"
        return value[:4] + "..." + value[-3:]

    @staticmethod
    def hash(value: Any, **kwargs) -> str:
        return "hash:" + hashlib.sha256(str(value).encode()).hexdigest()[:12]

    @staticmethod
    def remove(value: Any, **kwargs) -> str:
        return "<removed>"

    STRATEGIES: Dict[MaskingStrategy, Callable] = {
        MaskingStrategy.REDACT: redact,
        MaskingStrategy.PARTIAL: partial,
        MaskingStrategy.HASH: hash,
        MaskingStrategy.REMOVE: remove,
    }

    @classmethod
    def apply(cls, strategy: MaskingStrategy, value: Any, **kwargs) -> str:
        func = cls.STRATEGIES.get(strategy, cls.redact)
        return func(value, **kwargs)


# ==========================================================
# 7. ✅ Cache Key Normalization (من الجزء 2)
# ==========================================================

def _freeze(value: Any) -> Any:
    """
    تحويل أي قيمة إلى شكل ثابت وقابل للتجزئة (hashable).

    ✅ يحل مشاكل:
    - set غير مرتب → tuple مرتب
    - id() غير مستقر → qualname أو pattern
    - dict داخل list داخل tuple → تطبيع متداخل

    ✅ Deterministic: نفس الإعدادات تنتج دائماً نفس المفتاح.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float, str)):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, re.Pattern):
        # ✅ pattern + flags ثابتان عبر التشغيلات
        return f"regex:{value.pattern}:{value.flags}"

    if isinstance(value, Path):
        # ✅ resolve() يعطي مساراً مطلقاً ثابتاً
        return f"path:{value.resolve()}"

    if isinstance(value, dict):
        return tuple(
            sorted((k, _freeze(v)) for k, v in value.items())
        )

    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)

    if isinstance(value, (set, frozenset)):
        # ✅ sorted يحل مشكلة عدم ترتيب set
        return tuple(sorted(_freeze(v) for v in value))

    if callable(value):
        # ✅ qualname ثابت بدلاً من id() المتغير
        return f"callable:{getattr(value, '__qualname__', repr(value))}"

    # Fallback: repr ثابت
    return f"repr:{repr(value)}"


# ==========================================================
# 8. Sensitive Data Filter
# ==========================================================

class SensitiveDataFilter(logging.Filter):
    def __init__(
            self,
            patterns: Optional[Tuple[re.Pattern, ...]] = None,
            include_pii: bool = False,
            sensitive_keys: Optional[Tuple[str, ...]] = None,
            masking_strategy: MaskingStrategy = MaskingStrategy.REDACT,
            redaction_text: str = "***REDACTED***",
    ):
        super().__init__()

        base_patterns = patterns or DEFAULT_SECRET_PATTERNS
        if include_pii:
            base_patterns = base_patterns + DEFAULT_PII_PATTERNS

        self._patterns = base_patterns
        self._sensitive_keys = sensitive_keys or DEFAULT_SENSITIVE_KEYS
        self._masking_strategy = masking_strategy
        self._redaction_text = redaction_text

        self._counter_lock = threading.Lock()
        self._mask_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_text(record.msg)

        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = self._sanitize_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize_dict(arg) if isinstance(arg, dict) else arg
                    for arg in record.args
                )

        for attr in ('extra_data', 'sensitive_data', 'context_data'):
            if hasattr(record, attr):
                value = getattr(record, attr)
                if isinstance(value, dict):
                    setattr(record, attr, self._sanitize_dict(value))

        return True

    def _sanitize_text(self, text: str) -> str:
        for pattern in self._patterns:
            text = pattern.sub(self._mask_match, text)
        return text

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                sanitized[key] = self._get_masked_value(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_text(value)
            else:
                sanitized[key] = value
        return sanitized

    def _is_sensitive_key(self, key: str) -> bool:
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self._sensitive_keys)

    def _get_masked_value(self, value: Any) -> str:
        return MaskingStrategies.apply(
            self._masking_strategy,
            value,
            redaction_text=self._redaction_text
        )

    def _mask_match(self, match: re.Match) -> str:
        with self._counter_lock:
            self._mask_count += 1

        groups = match.groups()
        if len(groups) >= 2:
            return f"{groups[0]}={self._redaction_text}"
        return self._redaction_text

    @property
    def mask_count(self) -> int:
        return self._mask_count


# ==========================================================
# 9. Context Filter (contextvars — asyncio-ready)
# ==========================================================

class ContextFilter(logging.Filter):
    _request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
        'request_id', default='-'
    )
    _correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
        'correlation_id', default='-'
    )
    _user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
        'user_id', default='-'
    )

    def __init__(
            self,
            environment: str = "unknown",
            application: str = "HALALIA",
            version: str = "1.0.0",
            hostname: Optional[str] = None,
            machine_id: Optional[str] = None,
            worker_id: Optional[str] = None,
    ):
        super().__init__()
        self._environment = environment
        self._application = application
        self._version = version

        self._hostname = hostname or socket.gethostname()
        self._machine_id = machine_id or self._get_machine_id()
        self._worker_id = worker_id or f"{os.getpid()}-{threading.get_ident()}"

    @staticmethod
    def _get_machine_id() -> str:
        try:
            import platform
            return platform.node()
        except Exception:
            return "unknown"

    def set_request_id(self, request_id: str) -> contextvars.Token:
        return self._request_id_var.set(request_id)

    def get_request_id(self) -> str:
        return self._request_id_var.get()

    def reset_request_id(self, token: contextvars.Token) -> None:
        self._request_id_var.reset(token)

    def set_correlation_id(self, correlation_id: str) -> contextvars.Token:
        return self._correlation_id_var.set(correlation_id)

    def get_correlation_id(self) -> str:
        return self._correlation_id_var.get()

    def set_user_id(self, user_id: str) -> contextvars.Token:
        return self._user_id_var.set(user_id)

    def get_user_id(self) -> str:
        return self._user_id_var.get()

    @contextmanager
    def request_context(
            self,
            request_id: str,
            correlation_id: Optional[str] = None,
            user_id: Optional[str] = None,
    ):
        request_token = self.set_request_id(request_id)
        correlation_token = None
        user_token = None

        if correlation_id:
            correlation_token = self.set_correlation_id(correlation_id)
        if user_id:
            user_token = self.set_user_id(user_id)

        try:
            yield
        finally:
            self.reset_request_id(request_token)
            if correlation_token:
                self._correlation_id_var.reset(correlation_token)
            if user_token:
                self._user_id_var.reset(user_token)

    def filter(self, record: logging.LogRecord) -> bool:
        record.environment = self._environment
        record.application = self._application
        record.version = self._version

        record.hostname = self._hostname
        record.machine_id = self._machine_id
        record.worker_id = self._worker_id

        record.request_id = self.get_request_id()
        record.correlation_id = self.get_correlation_id()
        record.user_id = self.get_user_id()
        record.thread_name = threading.current_thread().name
        record.thread_id = threading.get_ident()
        record.process_id = record.process
        record.process_name = record.processName

        return True


# ==========================================================
# 10. Level Filter
# ==========================================================

class LevelFilter(logging.Filter):
    def __init__(
            self,
            min_level: int = logging.DEBUG,
            max_level: int = logging.CRITICAL,
            exclude_levels: Optional[Tuple[int, ...]] = None,
    ):
        super().__init__()
        self._min_level = min_level
        self._max_level = max_level
        self._exclude_levels = set(exclude_levels or ())

    def filter(self, record: logging.LogRecord) -> bool:
        level = record.levelno

        if level < self._min_level or level > self._max_level:
            return False

        if level in self._exclude_levels:
            return False

        return True


# ==========================================================
# 11. Module Filter (fnmatch)
# ==========================================================

class ModuleFilter(logging.Filter):
    def __init__(
            self,
            include_patterns: Optional[Tuple[str, ...]] = None,
            exclude_patterns: Optional[Tuple[str, ...]] = None,
            match_mode: str = "fnmatch",
    ):
        super().__init__()
        self._include_patterns = include_patterns or ()
        self._exclude_patterns = exclude_patterns or ()
        self._match_mode = match_mode

    def filter(self, record: logging.LogRecord) -> bool:
        logger_name = record.name
        module = record.module

        if self._include_patterns:
            if not self._matches_any(logger_name, module, self._include_patterns):
                return False

        if self._exclude_patterns:
            if self._matches_any(logger_name, module, self._exclude_patterns):
                return False

        return True

    def _matches_any(self, logger_name: str, module: str, patterns: Tuple[str, ...]) -> bool:
        for pattern in patterns:
            if self._match_mode == "fnmatch":
                if fnmatch.fnmatch(logger_name, pattern) or fnmatch.fnmatch(module, pattern):
                    return True
            elif self._match_mode == "exact":
                if logger_name == pattern or module == pattern:
                    return True
            elif self._match_mode == "substring":
                if pattern in logger_name or pattern in module:
                    return True
        return False


# ==========================================================
# 12. Message Pattern Filter
# ==========================================================

class MessagePatternFilter(logging.Filter):
    def __init__(
            self,
            include_patterns: Optional[Tuple[str, ...]] = None,
            exclude_patterns: Optional[Tuple[str, ...]] = None,
            ignore_case: bool = False,
    ):
        super().__init__()
        flags = re.IGNORECASE if ignore_case else 0

        self._include_patterns = [
            re.compile(p, flags) for p in (include_patterns or ())
        ]
        self._exclude_patterns = [
            re.compile(p, flags) for p in (exclude_patterns or ())
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()

        if self._include_patterns:
            if not any(p.search(message) for p in self._include_patterns):
                return False

        if self._exclude_patterns:
            if any(p.search(message) for p in self._exclude_patterns):
                return False

        return True


# ==========================================================
# 13. Rate Limit Filter (TTL/GC)
# ==========================================================

class RateLimitFilter(logging.Filter):
    def __init__(
            self,
            max_calls: int = DEFAULT_RATE_LIMIT_MAX_CALLS,
            window_seconds: float = DEFAULT_RATE_LIMIT_WINDOW,
            per_logger: bool = True,
            bucket_ttl: float = DEFAULT_RATE_LIMIT_TTL,
    ):
        super().__init__()
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._per_logger = per_logger
        self._bucket_ttl = bucket_ttl

        self._buckets: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        self._dropped_count = 0
        self._allowed_count = 0
        self._last_cleanup = time.monotonic()

    def filter(self, record: logging.LogRecord) -> bool:
        bucket_key = record.name if self._per_logger else "__global__"

        with self._lock:
            now = time.monotonic()
            if now - self._last_cleanup > 300:
                self._cleanup_expired_buckets(now)
                self._last_cleanup = now

            if bucket_key not in self._buckets:
                self._buckets[bucket_key] = {
                    "tokens": self._max_calls,
                    "last_refill": now,
                    "created_at": now,
                }

            bucket = self._buckets[bucket_key]

            elapsed = now - bucket["last_refill"]
            refill_rate = self._max_calls / self._window_seconds
            bucket["tokens"] = min(
                self._max_calls,
                bucket["tokens"] + elapsed * refill_rate
            )
            bucket["last_refill"] = now

            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                self._allowed_count += 1
                return True
            else:
                self._dropped_count += 1
                return False

    def _cleanup_expired_buckets(self, now: float) -> None:
        expired_keys = [
            key for key, bucket in self._buckets.items()
            if now - bucket["created_at"] > self._bucket_ttl
        ]
        for key in expired_keys:
            del self._buckets[key]

    @property
    def dropped_count(self) -> int:
        return self._dropped_count

    @property
    def allowed_count(self) -> int:
        return self._allowed_count

    @property
    def bucket_count(self) -> int:
        with self._lock:
            return len(self._buckets)

    def reset(self, logger_name: Optional[str] = None) -> None:
        with self._lock:
            if logger_name:
                key = logger_name if self._per_logger else "__global__"
                if key in self._buckets:
                    del self._buckets[key]
            else:
                self._buckets.clear()


# ==========================================================
# 14. Null Filter
# ==========================================================

class NullFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return True


# ==========================================================
# 15. Filter Factory (✅ مع _freeze() الجديد)
# ==========================================================

class FilterFactory:
    _instance: Optional["FilterFactory"] = None
    _lock = threading.Lock()

    _CACHEABLE_TYPES = frozenset({
        FilterType.SENSITIVE_DATA,
        FilterType.RATE_LIMIT,
    })

    def __new__(cls) -> "FilterFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._cache: Dict[Tuple, logging.Filter] = {}
        self._cache_lock = threading.RLock()

        self._creation_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._frozen = False

        self._custom_filters: Dict[str, FilterFactoryCallable] = {}
        self._registry_lock = threading.RLock()

    def create(
            self,
            filter_type: FilterType,
            **kwargs
    ) -> logging.Filter:
        # ✅ Cache Key Deterministic عبر _freeze()
        cache_key = (filter_type.value, _freeze(kwargs))

        should_cache = filter_type in self._CACHEABLE_TYPES

        if should_cache:
            with self._cache_lock:
                if cache_key in self._cache:
                    self._cache_hits += 1
                    return self._cache[cache_key]
                self._cache_misses += 1

        fltr = self._build_filter(filter_type, **kwargs)
        self._creation_count += 1

        if should_cache:
            with self._cache_lock:
                self._cache[cache_key] = fltr

        return fltr

    def _build_filter(
            self,
            filter_type: FilterType,
            **kwargs
    ) -> logging.Filter:
        with self._registry_lock:
            if filter_type.value in self._custom_filters:
                return self._custom_filters[filter_type.value](**kwargs)

        if filter_type == FilterType.SENSITIVE_DATA:
            return SensitiveDataFilter(**kwargs)
        elif filter_type == FilterType.CONTEXT:
            return ContextFilter(**kwargs)
        elif filter_type == FilterType.LEVEL:
            return LevelFilter(**kwargs)
        elif filter_type == FilterType.MODULE:
            return ModuleFilter(**kwargs)
        elif filter_type == FilterType.MESSAGE_PATTERN:
            return MessagePatternFilter(**kwargs)
        elif filter_type == FilterType.RATE_LIMIT:
            return RateLimitFilter(**kwargs)
        elif filter_type == FilterType.NULL:
            return NullFilter()
        else:
            raise UnknownFilterError(
                filter_type.value,
                self.supported_filters()
            )

    def create_from_string(
            self,
            filter_name: str,
            environment: str = "development",
            **kwargs
    ) -> logging.Filter:
        try:
            filter_type = FilterType(filter_name.lower())
            return self.create(filter_type, **kwargs)
        except ValueError:
            with self._registry_lock:
                if filter_name.lower() in self._custom_filters:
                    return self._custom_filters[filter_name.lower()](**kwargs)

            is_production = environment.lower() in ("production", "prod")

            if is_production:
                raise UnknownFilterError(
                    filter_name,
                    self.supported_filters()
                )
            else:
                warnings.warn(
                    f"Unknown filter '{filter_name}', falling back to NullFilter. "
                    f"Check APP_FILTER configuration.",
                    stacklevel=2
                )
                return self.create(FilterType.NULL, **kwargs)

    def register_filter(
            self,
            name: str,
            factory_func: FilterFactoryCallable
    ) -> None:
        if self._frozen:
            raise RuntimeError("Cannot register filter after factory is frozen.")

        if not name or not isinstance(name, str):
            raise ValueError("Filter name must be a non-empty string")

        if not callable(factory_func):
            raise TypeError("factory_func must be callable")

        normalized_name = name.lower()
        built_in_names = tuple(t.value for t in FilterType)

        if normalized_name in built_in_names:
            raise FilterRegistrationError(normalized_name, built_in_names)

        with self._registry_lock:
            self._custom_filters[normalized_name] = factory_func

    def unregister_filter(self, name: str) -> bool:
        if self._frozen:
            raise RuntimeError("Cannot unregister filter after factory is frozen.")

        with self._registry_lock:
            if name.lower() in self._custom_filters:
                del self._custom_filters[name.lower()]
                return True
            return False

    def supported_filters(self) -> Tuple[str, ...]:
        with self._registry_lock:
            built_in = tuple(t.value for t in FilterType)
            custom = tuple(self._custom_filters.keys())
            return built_in + custom

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def clear_cache(self) -> int:
        if self._frozen:
            raise RuntimeError("Cannot clear cache after factory is frozen.")

        with self._cache_lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def clear_registry(self) -> int:
        if self._frozen:
            raise RuntimeError("Cannot clear registry after factory is frozen.")

        with self._registry_lock:
            count = len(self._custom_filters)
            self._custom_filters.clear()
            return count

    @property
    def creation_count(self) -> int:
        return self._creation_count

    @property
    def cache_hits(self) -> int:
        return self._cache_hits

    @property
    def cache_misses(self) -> int:
        return self._cache_misses

    @property
    def cache_size(self) -> int:
        with self._cache_lock:
            return len(self._cache)

    @property
    def registered_custom_filters(self) -> int:
        with self._registry_lock:
            return len(self._custom_filters)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "version": FILTERS_VERSION,
            "creation_count": self._creation_count,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": self.cache_size,
            "registered_custom_filters": self.registered_custom_filters,
            "supported_types": self.supported_filters(),
            "frozen": self._frozen,
        }

    @property
    def version(self) -> str:
        return FILTERS_VERSION

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def __repr__(self) -> str:
        return (
            f"<FilterFactory "
            f"cache={self.cache_size} "
            f"created={self._creation_count} "
            f"custom={self.registered_custom_filters} "
            f"hits={self._cache_hits} "
            f"misses={self._cache_misses} "
            f"frozen={self._frozen}>"
        )


# ==========================================================
# 16. Global Instance
# ==========================================================
filter_factory = FilterFactory()


# ==========================================================
# 17. Convenience Functions
# ==========================================================

def get_sensitive_data_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.SENSITIVE_DATA, **kwargs)


def get_context_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.CONTEXT, **kwargs)


def get_level_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.LEVEL, **kwargs)


def get_module_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.MODULE, **kwargs)


def get_message_pattern_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.MESSAGE_PATTERN, **kwargs)


def get_rate_limit_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.RATE_LIMIT, **kwargs)


def get_null_filter(**kwargs) -> logging.Filter:
    return filter_factory.create(FilterType.NULL, **kwargs)


# ==========================================================
# 18. Explicit Public API
# ==========================================================
__all__ = [
    "FILTERS_VERSION",
    "FilterType",
    "MaskingStrategy",
    "MaskingStrategies",
    "UnknownFilterError",
    "FilterRegistrationError",
    "FilterFactoryCallable",
    "_freeze",  # ✅ مُصدّر للاختبارات والاستخدام الخارجي
    "SensitiveDataFilter",
    "ContextFilter",
    "LevelFilter",
    "ModuleFilter",
    "MessagePatternFilter",
    "RateLimitFilter",
    "NullFilter",
    "FilterFactory",
    "filter_factory",
    "get_sensitive_data_filter",
    "get_context_filter",
    "get_level_filter",
    "get_module_filter",
    "get_message_pattern_filter",
    "get_rate_limit_filter",
    "get_null_filter",
    "DEFAULT_SECRET_PATTERNS",
    "DEFAULT_PII_PATTERNS",
    "DEFAULT_SENSITIVE_KEYS",
    "DEFAULT_RATE_LIMIT_WINDOW",
    "DEFAULT_RATE_LIMIT_MAX_CALLS",
    "DEFAULT_RATE_LIMIT_TTL",
]