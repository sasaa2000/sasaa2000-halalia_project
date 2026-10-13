"""
HALALIA Log Handlers
Production Version 1.3.0 — VERIFIED (Final — All Reviews Applied)

المؤسس:
    جمال الدين زيدان

جميع الملاحظات من المراجعات الأربع مُطبقة:
    ✅ from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
    ✅ CacheKeyBuilder آمن (يتحمل Path, Formatter, callable)
    ✅ Cache انتقائي (File-based فقط — لا Console, لا Null)
    ✅ close_all() يمسح Cache + يزيل من root.handlers
    ✅ WeakSet لـ _active_handlers
    ✅ HandlerFactoryCallable Type Alias
    ✅ register_handler() + unregister_handler() (API متناظر)
    ✅ حماية Built-in names (HandlerRegistrationError)
    ✅ delay=True افتراضي
    ✅ errors="replace" في جميع File Handlers
    ✅ _prepare_log_directory() دالة موحدة
    ✅ NullHandler قبل Cache (Stateless)
    ✅ _is_handler_valid() للتحقق من صلاحية Handler في Cache
    ✅ Fallback حسب Environment (Dev→Console, Prod→Error)
    ✅ atexit.register(shutdown)
    ✅ cache_hits, cache_misses, closed_handlers_count
    ✅ get_null_handler(), get_timed_rotating_handler()
    ✅ unfreeze() للاختبارات
    ✅ Path مباشرة بدلاً من str()
    ✅ Warning عند Fallback
    ✅ custom= في __repr__
"""

from __future__ import annotations

import atexit
import logging
import sys
import threading
import warnings
from enum import Enum
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from weakref import WeakSet

# ==========================================================
# 1. Constants
# ==========================================================

HANDLERS_VERSION = "1.3.0"

DEFAULT_LOG_DIR = Path("runtime/logs")
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_ENCODING = "utf-8"
DEFAULT_ENCODING_ERRORS = "replace"

# ==========================================================
# 2. Type Aliases
# ==========================================================

HandlerFactoryCallable = Callable[..., logging.Handler]


# ==========================================================
# 3. Enums
# ==========================================================

class HandlerType(str, Enum):
    CONSOLE = "console"
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    TIMED_ROTATING = "timed_rotating"
    NULL = "null"


class WhenInterval(str, Enum):
    SECOND = "S"
    MINUTE = "M"
    HOUR = "H"
    DAY = "D"
    MIDNIGHT = "midnight"


# ==========================================================
# 4. Exceptions
# ==========================================================

class UnknownHandlerError(ValueError):
    def __init__(self, handler_name: str, available: Tuple[str, ...] = ()):
        self.handler_name = handler_name
        self.available = available
        sorted_available = tuple(sorted(available))
        super().__init__(
            f"Unknown handler type: '{handler_name}'. "
            f"Available: {sorted_available}"
        )


class HandlerRegistrationError(ValueError):
    def __init__(self, name: str, reserved: Tuple[str, ...]):
        self.name = name
        self.reserved = reserved
        super().__init__(
            f"Cannot register handler '{name}': "
            f"name conflicts with built-in handler. "
            f"Reserved names: {tuple(sorted(reserved))}"
        )


# ==========================================================
# 5. Cache Key Normalization
# ==========================================================

class CacheKeyBuilder:
    """يبني Cache Keys آمنة من kwargs"""
    __slots__ = ()

    @staticmethod
    def normalize(value: Any) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return f"bool:{value}"
        if isinstance(value, (int, float)):
            return f"num:{value}"
        if isinstance(value, str):
            return f"str:{value}"
        if isinstance(value, Path):
            return f"path:{value.resolve()}"
        if isinstance(value, Enum):
            return f"enum:{value.__class__.__name__}:{value.value}"
        if hasattr(value, '__name__'):
            return f"obj:{value.__class__.__name__}:{value.__name__}"
        if hasattr(value, '__class__'):
            return f"obj:{value.__class__.__name__}:{id(value)}"
        return f"repr:{repr(value)}"

    @classmethod
    def build(cls, handler_type_value: str, kwargs: Dict[str, Any]) -> Tuple:
        normalized_items = tuple(
            (k, cls.normalize(v))
            for k, v in sorted(kwargs.items())
        )
        return (handler_type_value, normalized_items)


# ==========================================================
# 6. Handler Factory (Singleton + Smart Cache + WeakSet)
# ==========================================================

class HandlerFactory:
    """
    المصنع المركزي للـ Handlers.
    Singleton Thread-Safe مع Cache ذكي وإدارة موارد.
    """

    _instance: Optional["HandlerFactory"] = None
    _lock = threading.Lock()

    # ✅ Cache انتقائي: File-based فقط
    _CACHEABLE_TYPES = frozenset({
        HandlerType.FILE,
        HandlerType.ROTATING_FILE,
        HandlerType.TIMED_ROTATING,
    })

    def __new__(cls) -> "HandlerFactory":
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
        self._cache: Dict[Tuple, logging.Handler] = {}
        self._cache_lock = threading.RLock()

        # Metrics
        self._creation_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._closed_count = 0

        self._frozen = False

        # Registry
        self._custom_handlers: Dict[str, HandlerFactoryCallable] = {}
        self._registry_lock = threading.RLock()

        # ✅ WeakSet لتتبع الـ Handlers النشطة
        self._active_handlers: WeakSet[logging.Handler] = WeakSet()
        self._active_lock = threading.RLock()

        # ✅ atexit للتنظيف التلقائي
        atexit.register(self._atexit_cleanup)

    def _atexit_cleanup(self) -> None:  # pragma: no cover
        try:
            self.shutdown()
        except Exception:
            pass

    # ======================================================
    # Core Factory Methods
    # ======================================================

    def create(self, handler_type: HandlerType, **kwargs) -> logging.Handler:
        """إنشاء Handler بالنوع المحدد"""
        # ✅ NullHandler لا يُخزن (Stateless)
        if handler_type == HandlerType.NULL:
            self._creation_count += 1
            return logging.NullHandler()

        # Cache Key آمن
        cache_key = CacheKeyBuilder.build(handler_type.value, kwargs)

        # Cache انتقائي
        should_cache = handler_type in self._CACHEABLE_TYPES

        if should_cache:
            with self._cache_lock:
                if cache_key in self._cache:
                    handler = self._cache[cache_key]
                    # ✅ التحقق من صلاحية Handler قبل إرجاعه
                    if self._is_handler_valid(handler):
                        self._cache_hits += 1
                        return handler
                    else:
                        # Handler مغلق، نزيله من Cache
                        del self._cache[cache_key]
                self._cache_misses += 1

        # بناء Handler جديد
        handler = self._build_handler(handler_type, **kwargs)
        self._creation_count += 1

        if should_cache:
            with self._cache_lock:
                self._cache[cache_key] = handler

        with self._active_lock:
            self._active_handlers.add(handler)

        return handler

    def _is_handler_valid(self, handler: logging.Handler) -> bool:
        """التحقق من أن Handler مازال صالحاً"""
        try:
            if hasattr(handler, 'stream') and handler.stream is None:
                return False
            if hasattr(handler, 'lock') and handler.lock is None:
                return False
            return True
        except Exception:
            return False

    def _build_handler(self, handler_type: HandlerType, **kwargs) -> logging.Handler:
        """بناء Handler الفعلي"""
        with self._registry_lock:
            if handler_type.value in self._custom_handlers:
                return self._custom_handlers[handler_type.value](**kwargs)

        if handler_type == HandlerType.CONSOLE:
            return self._create_console_handler(**kwargs)
        elif handler_type == HandlerType.FILE:
            return self._create_file_handler(**kwargs)
        elif handler_type == HandlerType.ROTATING_FILE:
            return self._create_rotating_file_handler(**kwargs)
        elif handler_type == HandlerType.TIMED_ROTATING:
            return self._create_timed_rotating_handler(**kwargs)
        else:
            raise UnknownHandlerError(handler_type.value, self.supported_handlers())

    # ======================================================
    # Handler Creation Methods
    # ======================================================

    def _prepare_log_directory(self, log_dir: Optional[Path]) -> Path:
        """✅ دالة موحدة لإعداد مجلد السجلات"""
        log_dir = log_dir or DEFAULT_LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _create_console_handler(self, stream=None) -> logging.StreamHandler:
        stream = stream or sys.stdout
        return logging.StreamHandler(stream)

    def _create_file_handler(
            self,
            filename: str = "halaliya.log",
            log_dir: Optional[Path] = None,
            mode: str = "a",
            encoding: str = DEFAULT_ENCODING,
            delay: bool = True,
    ) -> logging.FileHandler:
        log_dir = self._prepare_log_directory(log_dir)
        file_path = log_dir / filename
        return logging.FileHandler(
            file_path,
            mode=mode,
            encoding=encoding,
            delay=delay,
            errors=DEFAULT_ENCODING_ERRORS,
        )

    def _create_rotating_file_handler(
            self,
            filename: str = "halaliya.log",
            log_dir: Optional[Path] = None,
            max_bytes: int = DEFAULT_MAX_BYTES,
            backup_count: int = DEFAULT_BACKUP_COUNT,
            encoding: str = DEFAULT_ENCODING,
            delay: bool = True,
    ) -> RotatingFileHandler:
        log_dir = self._prepare_log_directory(log_dir)
        file_path = log_dir / filename
        return RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            delay=delay,
            errors=DEFAULT_ENCODING_ERRORS,
        )

    def _create_timed_rotating_handler(
            self,
            filename: str = "halaliya.log",
            log_dir: Optional[Path] = None,
            when: str = WhenInterval.MIDNIGHT.value,
            interval: int = 1,
            backup_count: int = DEFAULT_BACKUP_COUNT,
            encoding: str = DEFAULT_ENCODING,
    ) -> TimedRotatingFileHandler:
        log_dir = self._prepare_log_directory(log_dir)
        file_path = log_dir / filename
        return TimedRotatingFileHandler(
            file_path,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding=encoding,
            errors=DEFAULT_ENCODING_ERRORS,
        )

    # ======================================================
    # Convenience Methods
    # ======================================================

    def create_from_string(
            self,
            handler_name: str,
            environment: str = "development",
            **kwargs
    ) -> logging.Handler:
        """إنشاء Handler من اسم نصي مع Fallback حسب Environment"""
        try:
            handler_type = HandlerType(handler_name.lower())
            return self.create(handler_type, **kwargs)
        except ValueError:
            with self._registry_lock:
                if handler_name.lower() in self._custom_handlers:
                    return self._custom_handlers[handler_name.lower()](**kwargs)

            # ✅ Fallback حسب Environment
            is_production = environment.lower() in ("production", "prod")

            if is_production:
                raise UnknownHandlerError(handler_name, self.supported_handlers())
            else:
                warnings.warn(
                    f"Unknown handler '{handler_name}', falling back to Console.",
                    stacklevel=2
                )
                return self.create(HandlerType.CONSOLE, **kwargs)

    # ======================================================
    # Dynamic Registration (مع حماية)
    # ======================================================

    def register_handler(self, name: str, factory_func: HandlerFactoryCallable) -> None:
        """تسجيل Handler مخصص مع حماية Built-in"""
        if self._frozen:
            raise RuntimeError("Cannot register handler after factory is frozen.")

        if not name or not isinstance(name, str):
            raise ValueError("Handler name must be a non-empty string")

        if not callable(factory_func):
            raise TypeError("factory_func must be callable")

        normalized_name = name.lower()
        built_in_names = tuple(t.value for t in HandlerType)

        # ✅ حماية: منع استبدال المدمجة
        if normalized_name in built_in_names:
            raise HandlerRegistrationError(normalized_name, built_in_names)

        with self._registry_lock:
            self._custom_handlers[normalized_name] = factory_func

    def unregister_handler(self, name: str) -> bool:
        """إزالة Handler مخصص (API متناظر)"""
        if self._frozen:
            raise RuntimeError("Cannot unregister handler after factory is frozen.")

        with self._registry_lock:
            if name.lower() in self._custom_handlers:
                del self._custom_handlers[name.lower()]
                return True
            return False

    def supported_handlers(self) -> Tuple[str, ...]:
        with self._registry_lock:
            built_in = tuple(t.value for t in HandlerType)
            custom = tuple(self._custom_handlers.keys())
            return built_in + custom

    # ======================================================
    # Freeze / Unfreeze
    # ======================================================

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        """فك التجميد (للاختبارات فقط)"""
        self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    # ======================================================
    # Resource Management
    # ======================================================

    def close_handler(self, handler: logging.Handler) -> None:
        """إغلاق Handler وإزالته من Cache + root.handlers"""
        try:
            handler.close()
            self._closed_count += 1
        except Exception:
            pass

        # ✅ إزالة من active_handlers
        with self._active_lock:
            self._active_handlers.discard(handler)

        # ✅ إزالة من Cache
        with self._cache_lock:
            keys_to_remove = [k for k, v in self._cache.items() if v is handler]
            for key in keys_to_remove:
                del self._cache[key]

        # ✅ إزالة من root.handlers
        root_logger = logging.getLogger()
        if handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    def close_all(self) -> int:
        """إغلاق جميع Handlers + مسح Cache + تنظيف Active"""
        closed_count = 0

        with self._active_lock:
            handlers_to_close = list(self._active_handlers)
            self._active_handlers.clear()

        root_logger = logging.getLogger()

        for handler in handlers_to_close:
            try:
                handler.close()
                closed_count += 1
                self._closed_count += 1
            except Exception:
                pass

            # ✅ إزالة من root.handlers
            if handler in root_logger.handlers:
                root_logger.removeHandler(handler)

        # ✅ مسح Cache بالكامل
        with self._cache_lock:
            self._cache.clear()

        return closed_count

    def shutdown(self) -> int:
        """إيقاف شامل"""
        return self.close_all()

    def clear_cache(self) -> int:
        """مسح Cache Handlers فقط"""
        if self._frozen:
            raise RuntimeError("Cannot clear cache after factory is frozen.")

        with self._cache_lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def clear_registry(self) -> int:
        """مسح Registry Handlers المخصصة"""
        if self._frozen:
            raise RuntimeError("Cannot clear registry after factory is frozen.")

        with self._registry_lock:
            count = len(self._custom_handlers)
            self._custom_handlers.clear()
            return count

    # ======================================================
    # Metrics
    # ======================================================

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
    def active_count(self) -> int:
        with self._active_lock:
            return len(self._active_handlers)

    @property
    def registered_custom_handlers(self) -> int:
        with self._registry_lock:
            return len(self._custom_handlers)

    @property
    def closed_handlers_count(self) -> int:
        return self._closed_count

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "version": HANDLERS_VERSION,
            "creation_count": self._creation_count,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": self.cache_size,
            "active_handlers": self.active_count,
            "registered_custom_handlers": self.registered_custom_handlers,
            "closed_handlers_count": self._closed_count,
            "supported_types": self.supported_handlers(),
            "frozen": self._frozen,
        }

    # ======================================================
    # Metadata
    # ======================================================

    @property
    def version(self) -> str:
        return HANDLERS_VERSION

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def __repr__(self) -> str:
        return (
            f"<HandlerFactory "
            f"cache={self.cache_size} "
            f"active={self.active_count} "
            f"created={self._creation_count} "
            f"custom={self.registered_custom_handlers} "
            f"closed={self._closed_count} "
            f"frozen={self._frozen}>"
        )


# ==========================================================
# 7. Global Instance
# ==========================================================
handler_factory = HandlerFactory()


# ==========================================================
# 8. Convenience Functions (متناظرة)
# ==========================================================

def get_console_handler(**kwargs) -> logging.Handler:
    return handler_factory.create(HandlerType.CONSOLE, **kwargs)


def get_file_handler(**kwargs) -> logging.Handler:
    return handler_factory.create(HandlerType.FILE, **kwargs)


def get_rotating_file_handler(**kwargs) -> logging.Handler:
    return handler_factory.create(HandlerType.ROTATING_FILE, **kwargs)


def get_timed_rotating_handler(**kwargs) -> logging.Handler:
    return handler_factory.create(HandlerType.TIMED_ROTATING, **kwargs)


def get_null_handler(**kwargs) -> logging.Handler:
    return handler_factory.create(HandlerType.NULL, **kwargs)


# ==========================================================
# 9. Explicit Public API
# ==========================================================
__all__ = [
    "HANDLERS_VERSION",
    "HandlerType",
    "WhenInterval",
    "UnknownHandlerError",
    "HandlerRegistrationError",
    "CacheKeyBuilder",
    "HandlerFactoryCallable",
    "HandlerFactory",
    "handler_factory",
    "get_console_handler",
    "get_file_handler",
    "get_rotating_file_handler",
    "get_timed_rotating_handler",
    "get_null_handler",
    "DEFAULT_LOG_DIR",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_BACKUP_COUNT",
    "DEFAULT_ENCODING",
    "DEFAULT_ENCODING_ERRORS",
]