"""
HALALIA Configuration Service
Production Version 1.1 — VERIFIED (Final)

المؤسس: جمال الدين زيدان
الحالة: Production Complete ✅

التحسينات المطبقة:
    ✅ إصلاح ترتيب التهيئة (Profile قبل Load)
    ✅ إضافة SERVICE_VERSION و version property
    ✅ إضافة ready property (Runtime Gate)
    ✅ إنشاء ثابت CACHE_PREFIX
    ✅ إضافة ready إلى health_check
    ✅ تحسين __repr__
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .configuration_models import EnvironmentType
from .environment import EnvironmentManager, environment
from .configuration_cache import ConfigurationCache
from .configuration_sources import ConfigurationSourceManager, SourceFactory
from .configuration_profiles import ProfileManager
from .configuration_schema import ConfigurationSchema
from .configuration_validator import ConfigurationValidator

# ==========================================================
# 1. Constants
# ==========================================================

SERVICE_VERSION = "1.0.0"
CACHE_PREFIX = "CONFIG:"


# ==========================================================
# 2. Configuration Service (Facade)
# ==========================================================

class ConfigurationService:
    """
    الخدمة المركزية للإعدادات.
    Facade Pattern: تجمع جميع المكونات في واجهة واحدة بسيطة.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self._base_path = base_path or Path.cwd()
        self._lock = threading.RLock()
        self._initialized = False
        self._load_time_ms = 0.0

        # المكونات الأساسية (Lazy Initialization)
        self._environment: Optional[EnvironmentManager] = None
        self._sources: Optional[ConfigurationSourceManager] = None
        self._profiles: Optional[ProfileManager] = None
        self._cache: Optional[ConfigurationCache] = None
        self._schema: Optional[ConfigurationSchema] = None
        self._validator: Optional[ConfigurationValidator] = None

        # البيانات المحملة
        self._raw_config: Dict[str, Any] = {}
        self._final_config: Dict[str, Any] = {}

    # ======================================================
    # Lifecycle Management
    # ======================================================

    def initialize(self) -> None:
        """
        تهيئة الخدمة وتحميل جميع المكونات.
        يجب استدعاؤها مرة واحدة عند بدء التطبيق.
        """
        with self._lock:
            if self._initialized:
                return

            start_time = time.perf_counter()

            # 1. تهيئة Environment
            self._environment = environment

            # 2. تهيئة Sources
            self._sources = SourceFactory.create_default_manager(self._base_path)

            # 3. تهيئة Profiles
            self._profiles = ProfileManager()

            # ✅ التعديل 1: تعيين Profile النشط قبل التحميل
            env_name = self._environment.name
            if self._profiles.has_profile(env_name):
                self._profiles.set_active_profile(env_name)

            # 4. تهيئة Cache
            self._cache = ConfigurationCache(default_ttl=300.0)

            # 5. تهيئة Schema و Validator
            self._schema = ConfigurationSchema(name="halaliya_default")
            self._validator = ConfigurationValidator(schema=self._schema)

            # 6. تحميل الإعدادات (بعد تفعيل Profile)
            self._load_configurations()

            end_time = time.perf_counter()
            self._load_time_ms = (end_time - start_time) * 1000
            self._initialized = True

    def _load_configurations(self) -> None:
        """تحميل الإعدادات من المصادر وتطبيق Profile النشط"""
        # 1. تحميل من المصادر
        self._raw_config = self._sources.load_all()

        # 2. تطبيق Profile النشط
        self._final_config = self._profiles.apply_active_profile(self._raw_config)

        # 3. تخزين في الذاكرة المؤقتة (باستخدام CACHE_PREFIX الموحد)
        for key, value in self._final_config.items():
            self._cache.set(f"{CACHE_PREFIX}{key}", value, ttl=300.0)

    def reload(self) -> None:
        """إعادة تحميل الإعدادات (للتطوير والصيانة)"""
        with self._lock:
            self._cache.clear()
            self._load_configurations()

    # ======================================================
    # Public API - Read Operations
    # ======================================================

    def get(self, key: str, default: Any = None) -> Any:
        """
        الحصول على قيمة إعداد.
        يبحث أولاً في الذاكرة المؤقتة، ثم في الإعدادات النهائية.
        """
        if not self._initialized:
            raise RuntimeError("ConfigurationService not initialized. Call initialize() first.")

        # 1. البحث في الذاكرة المؤقتة (باستخدام CACHE_PREFIX الموحد)
        cached_value = self._cache.get(f"{CACHE_PREFIX}{key}")
        if cached_value is not None:
            return cached_value

        # 2. البحث في الإعدادات النهائية
        value = self._final_config.get(key, default)

        # 3. تخزين في الذاكرة المؤقتة
        if value is not None:
            self._cache.set(f"{CACHE_PREFIX}{key}", value, ttl=300.0)

        return value

    def get_int(self, key: str, default: int = 0) -> int:
        """الحصول على قيمة صحيحة"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """الحصول على قيمة منطقية"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on", "enabled")
        return default

    def get_str(self, key: str, default: str = "") -> str:
        """الحصول على قيمة نصية"""
        value = self.get(key, default)
        return str(value) if value is not None else default

    def has(self, key: str) -> bool:
        """التحقق من وجود مفتاح"""
        return key in self._final_config

    def keys(self) -> tuple:
        """إرجاع جميع المفاتيح"""
        return tuple(self._final_config.keys())

    def as_dict(self) -> Dict[str, Any]:
        """إرجاع جميع الإعدادات كقاموس (للقراءة فقط)"""
        return self._final_config.copy()

    # ======================================================
    # Public API - Component Access
    # ======================================================

    @property
    def environment(self) -> EnvironmentManager:
        if not self._initialized:
            raise RuntimeError("ConfigurationService not initialized.")
        return self._environment

    @property
    def cache(self) -> ConfigurationCache:
        if not self._initialized:
            raise RuntimeError("ConfigurationService not initialized.")
        return self._cache

    @property
    def profiles(self) -> ProfileManager:
        if not self._initialized:
            raise RuntimeError("ConfigurationService not initialized.")
        return self._profiles

    @property
    def sources(self) -> ConfigurationSourceManager:
        if not self._initialized:
            raise RuntimeError("ConfigurationService not initialized.")
        return self._sources

    # ======================================================
    # Validation
    # ======================================================

    def validate(self) -> Dict[str, Any]:
        """التحقق من صحة الإعدادات"""
        if not self._initialized:
            raise RuntimeError("ConfigurationService not initialized.")

        report = self._validator.validate(self._final_config)
        return report.to_dict()

    def is_valid(self) -> bool:
        """هل الإعدادات صالحة؟"""
        report = self._validator.validate(self._final_config)
        return report.is_valid

    # ======================================================
    # ✅ التعديل 3: Ready State (Runtime Gate)
    # ======================================================

    @property
    def ready(self) -> bool:
        """
        هل الخدمة جاهزة للاستخدام؟
        تُستخدم كـ Gate في Runtime قبل معالجة الطلبات.
        """
        return self._initialized and self.is_valid()

    # ======================================================
    # ✅ التعديل 2: Version
    # ======================================================

    @property
    def version(self) -> str:
        """إصدار خدمة الإعدادات"""
        return SERVICE_VERSION

    # ======================================================
    # Health & Metrics
    # ======================================================

    def health_check(self) -> Dict[str, Any]:
        """فحص صحة الخدمة"""
        if not self._initialized:
            return {
                "healthy": False,
                "reason": "Service not initialized"
            }

        return {
            "healthy": True,
            "ready": self.ready,  # ✅ التعديل 5
            "environment": self._environment.name,
            "is_production": self._environment.is_production,
            "cache_healthy": self._cache.healthy,
            "config_valid": self.is_valid(),
            "load_time_ms": round(self._load_time_ms, 2),
            "total_keys": len(self._final_config),
            "cache_size": self._cache.size,
            "sources_count": self._sources.source_count,
            "profiles_count": self._profiles.profile_count
        }

    def get_metrics(self) -> Dict[str, Any]:
        """إرجاع إحصائيات الأداء"""
        return {
            "version": SERVICE_VERSION,
            "load_time_ms": round(self._load_time_ms, 2),
            "cache_stats": self._cache.get_stats(),
            "sources_count": self._sources.source_count,
            "available_sources": self._sources.available_count,
            "profiles_count": self._profiles.profile_count,
            "total_keys": len(self._final_config)
        }

    # ======================================================
    # Metadata
    # ======================================================

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def to_dict(self) -> Dict[str, Any]:
        """تصدير حالة الخدمة كقاموس (للتسجيل)"""
        return {
            "version": SERVICE_VERSION,
            "initialized": self._initialized,
            "ready": self.ready,
            "environment": self._environment.name if self._initialized else None,
            "load_time_ms": round(self._load_time_ms, 2),
            "total_keys": len(self._final_config),
            "health": self.health_check() if self._initialized else None
        }

    # ✅ التعديل 6: تحسين __repr__
    def __repr__(self) -> str:
        env = self._environment.name if self._initialized else "unknown"
        return (
            f"<ConfigurationService "
            f"env={env} "
            f"ready={self.ready}>"
        )


# ==========================================================
# 3. Global Instance
# ==========================================================
config_service = ConfigurationService()

# ==========================================================
# 4. Explicit Public API
# ==========================================================
__all__ = [
    "ConfigurationService",
    "config_service",
    "SERVICE_VERSION",
    "CACHE_PREFIX",
]