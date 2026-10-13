"""
HALALIA Logger Factory
Production Version 1.4.1 - Fixed

Founder:
    Jamal Eldin Zidan

Fixes:
    - Restored a complete Python module after the source file was truncated.
    - Replaced corrupted Arabic comments/docstrings with valid text.
    - Added safe console and file handler helpers.
    - Preserved logger metadata, caching, and specialized logger access.
"""

from __future__ import annotations

import logging
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


FACTORY_VERSION = "1.4.1"


class LoggerName(str, Enum):
    SYSTEM = "HALALIA_SYSTEM"
    ERROR = "HALALIA_ERRORS"
    SECURITY = "HALALIA_SECURITY"
    AI = "HALALIA_AI"
    AUDIT = "HALALIA_AUDIT"
    PERFORMANCE = "HALALIA_PERFORMANCE"
    DATABASE = "HALALIA_DATABASE"
    NETWORK = "HALALIA_NETWORK"
    CACHE = "HALALIA_CACHE"
    CONFIG = "HALALIA_CONFIG"


class UnknownLoggerError(KeyError):
    """Raised when requesting an unknown specialized logger."""

    def __init__(self, logger_name: str):
        self.logger_name = logger_name
        available = tuple(logger.value for logger in LoggerName)
        super().__init__(
            f"Unknown specialized logger: '{logger_name}'. Available: {available}"
        )

    def __str__(self) -> str:
        return self.args[0] if self.args else ""  # pragma: no cover


class LoggerRegistrationError(ValueError):
    """Raised when an external logger cannot be registered."""

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"Cannot register logger '{name}': {reason}")


class LoggerFactory:
    _instance: Optional["LoggerFactory"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LoggerFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._logger_cache: Dict[str, logging.Logger] = {}
        self._metadata_lock = threading.RLock()
        self._specialized_loggers: Set[str] = set()
        self._frozen = False

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. Intended for tests."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
            cls._instance = None

    def get_logger(
        self,
        name: str,
        level: Optional[int] = None,
        propagate: bool = False,
    ) -> logging.Logger:
        if not isinstance(name, str) or not name.strip():
            raise LoggerRegistrationError(
                str(name),
                "name must be a non-empty string",
            )

        with self._metadata_lock:
            if name in self._logger_cache:
                logger = self._logger_cache[name]
                self._metadata[name]["access_count"] += 1
                if level is not None:
                    logger.setLevel(level)
                logger.propagate = propagate
                return logger

            logger = logging.getLogger(name)
            logger.propagate = propagate
            if level is not None:
                logger.setLevel(level)

            self._logger_cache[name] = logger
            self._metadata[name] = {
                "created_at": time.time(),
                "access_count": 1,
                "is_specialized": False,
                "external": False,
            }
            return logger

    def get_specialized(self, logger_enum: LoggerName) -> logging.Logger:
        if not isinstance(logger_enum, LoggerName):
            raise UnknownLoggerError(str(logger_enum))

        name = logger_enum.value
        logger = self.get_logger(name, propagate=False)
        with self._metadata_lock:
            self._metadata[name]["is_specialized"] = True
            self._specialized_loggers.add(name)
        return logger

    @property
    def system(self) -> logging.Logger:
        return self.get_specialized(LoggerName.SYSTEM)

    @property
    def error(self) -> logging.Logger:
        return self.get_specialized(LoggerName.ERROR)

    @property
    def security(self) -> logging.Logger:
        return self.get_specialized(LoggerName.SECURITY)

    @property
    def ai(self) -> logging.Logger:
        return self.get_specialized(LoggerName.AI)

    @property
    def audit(self) -> logging.Logger:
        return self.get_specialized(LoggerName.AUDIT)

    @property
    def performance(self) -> logging.Logger:
        return self.get_specialized(LoggerName.PERFORMANCE)

    @property
    def database(self) -> logging.Logger:
        return self.get_specialized(LoggerName.DATABASE)

    @property
    def network(self) -> logging.Logger:
        return self.get_specialized(LoggerName.NETWORK)

    @property
    def cache(self) -> logging.Logger:
        return self.get_specialized(LoggerName.CACHE)

    @property
    def config(self) -> logging.Logger:
        return self.get_specialized(LoggerName.CONFIG)

    def get_logger_with_console(
        self,
        name: str,
        level: Optional[int] = None,
        use_colors: bool = True,
    ) -> logging.Logger:
        """Create or return a logger with one stream handler."""
        logger = self.get_logger(name, level=level, propagate=False)

        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            handler = logging.StreamHandler()
            handler.setLevel(level if level is not None else logging.NOTSET)
            handler.setFormatter(self._build_formatter(use_colors=use_colors))
            logger.addHandler(handler)

        return logger

    def get_logger_with_file(
        self,
        name: str,
        file_path: str | Path,
        level: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> logging.Logger:
        """Create or return a logger with one file handler for the target path."""
        logger = self.get_logger(name, level=level, propagate=False)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path = str(path.resolve())

        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                if Path(handler.baseFilename).resolve() == Path(resolved_path):
                    return logger

        handler = logging.FileHandler(resolved_path, encoding=encoding)
        handler.setLevel(level if level is not None else logging.NOTSET)
        handler.setFormatter(self._build_formatter(use_colors=False))
        logger.addHandler(handler)
        return logger

    def register_external_logger(
        self,
        name: str,
        logger: logging.Logger,
        *,
        is_specialized: bool = False,
    ) -> logging.Logger:
        if not isinstance(name, str) or not name.strip():
            raise LoggerRegistrationError(str(name), "name must be a non-empty string")
        if not isinstance(logger, logging.Logger):
            raise LoggerRegistrationError(name, "logger must be an instance of logging.Logger")
        if self._frozen:
            raise LoggerRegistrationError(name, "factory registry is frozen")

        name = name.strip()
        with self._metadata_lock:
            self._logger_cache[name] = logger
            self._metadata[name] = {
                "created_at": time.time(),
                "access_count": 0,
                "is_specialized": is_specialized,
                "external": True,
            }

            if is_specialized:
                self._specialized_loggers.add(name)

        return logger

    def unregister_logger(self, name: str) -> bool:
        """Remove the logger from this factory registry.

        Python's logging module keeps global logger objects internally, so this
        does not delete the logger from logging.manager.loggerDict.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Logger name must be a non-empty string")
        if self._frozen:
            raise LoggerRegistrationError(name, "factory registry is frozen")

        name = name.strip()
        with self._metadata_lock:
            existed = name in self._logger_cache
            self._logger_cache.pop(name, None)
            self._metadata.pop(name, None)
            self._specialized_loggers.discard(name)
            return existed

    def initialize_specialized_loggers(
        self,
        level: Optional[int] = None,
        propagate: bool = False,
    ) -> Dict[LoggerName, logging.Logger]:
        initialized: Dict[LoggerName, logging.Logger] = {}
        for logger_name in LoggerName:
            logger = self.get_logger(logger_name.value, level=level, propagate=propagate)
            with self._metadata_lock:
                self._metadata[logger_name.value]["is_specialized"] = True
                self._specialized_loggers.add(logger_name.value)
            initialized[logger_name] = logger
        return initialized

    def get_metadata(self, name: Optional[str] = None) -> Dict[str, Any]:
        with self._metadata_lock:
            if name is not None:
                if name not in self._metadata:
                    raise UnknownLoggerError(name)
                return dict(self._metadata[name])
            return {key: dict(value) for key, value in self._metadata.items()}

    def list_loggers(self) -> List[str]:
        with self._metadata_lock:
            return sorted(self._logger_cache)

    def list_specialized_loggers(self) -> List[str]:
        with self._metadata_lock:
            return sorted(self._specialized_loggers)

    def freeze(self) -> None:
        with self._metadata_lock:
            self._frozen = True

    def unfreeze(self) -> None:
        with self._metadata_lock:
            self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    @staticmethod
    def _build_formatter(use_colors: bool = False) -> logging.Formatter:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

        if not use_colors:
            return logging.Formatter(fmt=fmt, datefmt=datefmt)

        return _ColorFormatter(fmt=fmt, datefmt=datefmt)


class _ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self.COLORS.get(record.levelno)
        if color is None:
            return message
        return f"{color}{message}{self.RESET}"


logger_factory = LoggerFactory()


def get_logger(
    name: str,
    level: Optional[int] = None,
    propagate: bool = False,
) -> logging.Logger:
    return logger_factory.get_logger(name, level=level, propagate=propagate)


def get_specialized(logger_enum: LoggerName) -> logging.Logger:
    return logger_factory.get_specialized(logger_enum)


def initialize_specialized_loggers(
    level: Optional[int] = None,
    propagate: bool = False,
) -> Dict[LoggerName, logging.Logger]:
    return logger_factory.initialize_specialized_loggers(
        level=level,
        propagate=propagate,
    )


__all__ = [
    "FACTORY_VERSION",
    "LoggerFactory",
    "LoggerName",
    "LoggerRegistrationError",
    "UnknownLoggerError",
    "get_logger",
    "get_specialized",
    "initialize_specialized_loggers",
    "logger_factory",
]
