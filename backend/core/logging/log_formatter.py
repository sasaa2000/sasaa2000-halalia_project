"""
HALALIA Log Formatter
Production Version 1.1 — VERIFIED (Final)
"""

from __future__ import annotations

import json
import logging
import os
import platform
import socket
import sys
import threading
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Dict, Optional, Tuple, Type

# ==========================================================
# 1. Constants & Version
# ==========================================================

FORMATTER_VERSION = "1.1.0"


# ==========================================================
# 2. AnsiColor
# ==========================================================

class AnsiColor:
    __slots__ = ()
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"


# ==========================================================
# 3. Enums
# ==========================================================

class FormatterType(str, Enum):
    CONSOLE = "console"
    JSON = "json"
    MINIMAL = "minimal"
    DETAILED = "detailed"
    RAW = "raw"


# ==========================================================
# 4. Level Mappings
# ==========================================================

LEVEL_COLORS: MappingProxyType = MappingProxyType({
    logging.DEBUG: AnsiColor.GRAY,
    logging.INFO: AnsiColor.GREEN,
    logging.WARNING: AnsiColor.YELLOW,
    logging.ERROR: AnsiColor.RED,
    logging.CRITICAL: AnsiColor.BOLD + AnsiColor.BG_RED + AnsiColor.WHITE,
})

LEVEL_NAMES: MappingProxyType = MappingProxyType({
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO ",
    logging.WARNING: "WARN ",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRIT ",
})


# ==========================================================
# 5. Exceptions
# ==========================================================

class UnknownFormatterError(ValueError):
    def __init__(self, formatter_name: str, available: Tuple[str, ...] = ()):
        self.formatter_name = formatter_name
        self.available = available
        super().__init__(
            f"Unknown formatter type: '{formatter_name}'. "
            f"Available: {available}"
        )


# ==========================================================
# 6. Timestamp Utility
# ==========================================================

class TimestampUtil:
    __slots__ = ()

    @staticmethod
    def utc_iso(record: logging.LogRecord, timespec: str = "milliseconds") -> str:
        return datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).isoformat(timespec=timespec)

    @staticmethod
    def utc_formatted(record: logging.LogRecord, fmt: str) -> str:
        return datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime(fmt)


# ==========================================================
# 7. System Metadata
# ==========================================================

class SystemMetadata:
    _cached: Optional[Dict[str, str]] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> Dict[str, str]:
        if cls._cached is None:
            with cls._lock:
                if cls._cached is None:
                    cls._cached = {
                        "hostname": socket.gethostname(),
                        "machine": platform.machine(),
                        "application": "HALALIA",
                        "version": "1.0.0",
                        "python_version": platform.python_version(),
                        "os": platform.system(),
                    }
        return cls._cached


# ==========================================================
# 8. Console Formatter
# ==========================================================

class ConsoleFormatter(logging.Formatter):
    DEFAULT_CONSOLE_FORMAT = "{timestamp} | {level} | {logger:<20} | {message}"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(
            self,
            fmt: Optional[str] = None,
            datefmt: Optional[str] = None,
            use_colors: bool = True,
            show_thread: bool = False,
            show_module: bool = False,
    ):
        super().__init__(
            fmt=fmt or self.DEFAULT_CONSOLE_FORMAT,
            datefmt=datefmt or self.DEFAULT_DATE_FORMAT,
            style="{",
        )
        self._use_colors = use_colors
        self._show_thread = show_thread
        self._show_module = show_module

    def _supports_color(self) -> bool:
        if not hasattr(sys.stdout, "isatty"):
            return False
        return sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        timestamp = TimestampUtil.utc_formatted(record, self.datefmt)

        level_name = LEVEL_NAMES.get(record.levelno, record.levelname)
        if self._use_colors:
            color = LEVEL_COLORS.get(record.levelno, "")
            level_display = f"{color}{level_name}{AnsiColor.RESET}"
        else:
            level_display = level_name

        message = record.getMessage()
        parts = [timestamp, level_display, f"{record.name:<20}", message]

        if self._show_thread:
            parts.insert(2, f"[{threading.current_thread().name}]")

        if self._show_module:
            parts.insert(2, f"({record.module}:{record.lineno})")

        output = " | ".join(parts)

        if record.exc_info:
            output += "\n" + self.formatException(record.exc_info)

        return output


# ==========================================================
# 9. JSON Formatter
# ==========================================================

class JsonFormatter(logging.Formatter):
    def __init__(
            self,
            include_context: bool = True,
            include_stack_trace: bool = True,
            include_source: bool = False,
            indent: Optional[int] = None,
            ensure_ascii: bool = False,
    ):
        super().__init__()
        self._include_context = include_context
        self._include_stack_trace = include_stack_trace
        self._include_source = include_source
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    def format(self, record: logging.LogRecord) -> str:
        system_meta = SystemMetadata.get()

        log_entry = {
            "timestamp": TimestampUtil.utc_iso(record),
            "level": record.levelname,
            "level_no": record.levelno,
            "logger": record.name,
            "message": record.getMessage(),
            "hostname": system_meta["hostname"],
            "machine": system_meta["machine"],
            "application": system_meta["application"],
            "version": system_meta["version"],
        }

        if self._include_source:
            log_entry["source"] = {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "pathname": record.pathname,
            }

        if self._include_context:
            log_entry["metadata"] = {
                "environment": getattr(record, "environment", "unknown"),
                "request_id": getattr(record, "request_id", "-"),
                "thread": threading.current_thread().name,
                "process": record.process,
                "process_name": record.processName,
            }

        if self._include_stack_trace and record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = record.extra_data

        return json.dumps(
            log_entry,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
            default=str,
        )


# ==========================================================
# 10. Minimal Formatter
# ==========================================================

class MinimalFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("%(message)s")

    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()


# ==========================================================
# 11. Detailed Formatter
# ==========================================================

class DetailedFormatter(logging.Formatter):
    DEFAULT_DETAILED_FORMAT = (
        "{timestamp} | {level:<8} | {logger:<25} | "
        "PID={process} | {module}:{lineno} | {funcName} | {thread} | {message}"
    )
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, datefmt: Optional[str] = None):
        super().__init__(
            fmt=self.DEFAULT_DETAILED_FORMAT,
            datefmt=datefmt or self.DEFAULT_DATE_FORMAT,
            style="{",
        )

    def format(self, record: logging.LogRecord) -> str:
        timestamp = TimestampUtil.utc_formatted(record, self.datefmt) + \
                    f".{int((record.created % 1) * 1000):03d}"

        output = self._fmt.format(
            timestamp=timestamp,
            level=record.levelname,
            logger=record.name,
            module=record.module,
            lineno=record.lineno,
            funcName=record.funcName,
            thread=threading.current_thread().name,
            process=record.process,
            message=record.getMessage(),
        )

        if record.exc_info:
            output += "\n" + self.formatException(record.exc_info)

        return output


# ==========================================================
# 12. Raw Formatter
# ==========================================================

class RawFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("%(message)s")

    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()


# ==========================================================
# 13. Formatter Factory
# ==========================================================

class FormatterFactory:
    _instance: Optional["FormatterFactory"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "FormatterFactory":
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
        self._cache: Dict[Tuple, logging.Formatter] = {}
        self._cache_lock = threading.RLock()
        self._creation_count = 0
        self._frozen = False
        self._custom_formatters: Dict[str, Callable[..., logging.Formatter]] = {}
        self._registry_lock = threading.RLock()

    def create(self, formatter_type: FormatterType, **kwargs) -> logging.Formatter:
        cache_key = (formatter_type, tuple(sorted(kwargs.items())))

        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

            formatter = self._build_formatter(formatter_type, **kwargs)
            self._cache[cache_key] = formatter
            self._creation_count += 1
            return formatter

    def _build_formatter(self, formatter_type: FormatterType, **kwargs) -> logging.Formatter:
        with self._registry_lock:
            if formatter_type.value in self._custom_formatters:
                return self._custom_formatters[formatter_type.value](**kwargs)

        if formatter_type == FormatterType.CONSOLE:
            return ConsoleFormatter(**kwargs)
        elif formatter_type == FormatterType.JSON:
            return JsonFormatter(**kwargs)
        elif formatter_type == FormatterType.MINIMAL:
            return MinimalFormatter()
        elif formatter_type == FormatterType.DETAILED:
            return DetailedFormatter(**kwargs)
        elif formatter_type == FormatterType.RAW:
            return RawFormatter()
        else:
            raise UnknownFormatterError(
                formatter_type.value,
                self.supported_formatters()
            )

    def create_from_string(self, formatter_name: str, **kwargs) -> logging.Formatter:
        try:
            formatter_type = FormatterType(formatter_name.lower())
            return self.create(formatter_type, **kwargs)
        except ValueError:
            with self._registry_lock:
                if formatter_name.lower() in self._custom_formatters:
                    return self._custom_formatters[formatter_name.lower()](**kwargs)
            return self.create(FormatterType.CONSOLE, **kwargs)

    def register_formatter(self, name: str, factory_func: Callable[..., logging.Formatter]) -> None:
        if self._frozen:
            raise RuntimeError(
                "Cannot register formatter after factory is frozen. "
                "Register before startup completes."
            )
        with self._registry_lock:
            self._custom_formatters[name.lower()] = factory_func

    def supported_formatters(self) -> Tuple[str, ...]:
        with self._registry_lock:
            built_in = tuple(t.value for t in FormatterType)
            custom = tuple(self._custom_formatters.keys())
            return built_in + custom

    def freeze(self) -> None:
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def clear_cache(self) -> int:
        with self._cache_lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    @property
    def cache_size(self) -> int:
        with self._cache_lock:
            return len(self._cache)

    @property
    def creation_count(self) -> int:
        return self._creation_count

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "version": FORMATTER_VERSION,
            "creation_count": self._creation_count,
            "cache_size": self.cache_size,
            "supported_types": self.supported_formatters(),
            "frozen": self._frozen,
        }

    @property
    def version(self) -> str:
        return FORMATTER_VERSION

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def __repr__(self) -> str:
        return (
            f"<FormatterFactory "
            f"cache={self.cache_size} "
            f"created={self._creation_count} "
            f"frozen={self._frozen}>"
        )


# ==========================================================
# 14. Global Instance
# ==========================================================
formatter_factory = FormatterFactory()


# ==========================================================
# 15. Convenience Functions
# ==========================================================

def get_console_formatter(**kwargs) -> logging.Formatter:
    return formatter_factory.create(FormatterType.CONSOLE, **kwargs)


def get_json_formatter(**kwargs) -> logging.Formatter:
    return formatter_factory.create(FormatterType.JSON, **kwargs)


# ==========================================================
# 16. Explicit Public API
# ==========================================================
__all__ = [
    "FORMATTER_VERSION",
    "AnsiColor",
    "FormatterType",
    "UnknownFormatterError",
    "TimestampUtil",
    "SystemMetadata",
    "ConsoleFormatter",
    "JsonFormatter",
    "MinimalFormatter",
    "DetailedFormatter",
    "RawFormatter",
    "FormatterFactory",
    "formatter_factory",
    "get_console_formatter",
    "get_json_formatter",
    "LEVEL_COLORS",
    "LEVEL_NAMES",
]