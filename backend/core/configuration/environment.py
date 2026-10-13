"""
HALALIA Environment Manager
Production Version 1.1 — VERIFIED

المؤسس: جمال الدين زيدان
الحالة: Production Ready ✅

التحسينات المطبقة:
    ✅ إضافة is_live (Production أو Staging)
    ✅ إضافة is_local (Development فقط)
    ✅ إضافة validate() للتحقق من البيئة
    ✅ إضافة reload() مع reset() كـ alias
    ✅ إزالة type: ignore لصالح assert
    ✅ إضافة id property للسجلات
"""

from __future__ import annotations

import os
import threading
from typing import Optional, Tuple

from .configuration_models import EnvironmentType, SUPPORTED_ENVIRONMENTS


# ==========================================================
# 1. Environment Manager
# ==========================================================

class EnvironmentManager:
    """
    مدير بيئة التشغيل (Singleton Thread-Safe).
    يوفر وصولاً سريعاً وموحداً لمعلومات البيئة الحالية.
    """

    ENV_VAR_NAME = "APP_ENVIRONMENT"
    DEFAULT_ENVIRONMENT = EnvironmentType.DEVELOPMENT

    _instance: Optional["EnvironmentManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EnvironmentManager":
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
        self._current: Optional[EnvironmentType] = None
        self._auto_detect()

    # ======================================================
    # Detection
    # ======================================================

    def _auto_detect(self) -> None:
        env_value = os.getenv(self.ENV_VAR_NAME, "").strip().lower()

        if not env_value:
            self._current = self.DEFAULT_ENVIRONMENT
            return

        try:
            self._current = EnvironmentType(env_value)
        except ValueError:
            self._current = self.DEFAULT_ENVIRONMENT

    # ======================================================
    # Public Query Interface
    # ======================================================

    def get(self) -> EnvironmentType:
        if self._current is None:
            self._auto_detect()

        # ✅ إزالة type: ignore لصالح assert
        assert self._current is not None
        return self._current

    @property
    def current(self) -> EnvironmentType:
        return self.get()

    @property
    def name(self) -> str:
        return self.get().value

    @property
    def id(self) -> str:
        """معرف البيئة للسجلات (Logs)"""
        return self.current.name

    # ======================================================
    # Boolean Query Properties
    # ======================================================

    @property
    def is_development(self) -> bool:
        return self.get() == EnvironmentType.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.get() == EnvironmentType.TESTING

    @property
    def is_staging(self) -> bool:
        return self.get() == EnvironmentType.STAGING

    @property
    def is_production(self) -> bool:
        return self.get() == EnvironmentType.PRODUCTION

    # ======================================================
    # Composite Query Properties
    # ======================================================

    @property
    def is_safe_for_debug(self) -> bool:
        return not self.is_production

    @property
    def requires_strict_security(self) -> bool:
        return self.is_production or self.is_staging

    @property
    def supports_hot_reload(self) -> bool:
        return self.is_development or self.is_testing

    @property
    def is_live(self) -> bool:
        """هل النظام يعمل في بيئة حقيقية؟ (Production أو Staging)"""
        return self.is_production or self.is_staging

    @property
    def is_local(self) -> bool:
        """هل النظام يعمل محلياً؟ (Development فقط)"""
        return self.is_development

    # ======================================================
    # Validation
    # ======================================================

    def validate(self) -> bool:
        """التحقق من أن البيئة الحالية صحيحة"""
        return self.current in self.supported_environments

    # ======================================================
    # Mutation
    # ======================================================

    def set(self, env: EnvironmentType) -> None:
        if self.is_live:  # ✅ يرفض في production و staging معاً
            raise RuntimeError(
                "Cannot manually change environment in a live environment "
                "(production or staging). Use environment variables instead."
            )
        self._current = env

    def reload(self) -> None:
        """إعادة اكتشاف البيئة من متغيرات البيئة"""
        self._current = None
        self._auto_detect()

    def reset(self) -> None:
        """Alias لـ reload()"""
        self.reload()

    # سطر فارغ إضافي لتحسين التنسيق بين الدوال والخصائص (تمت الإضافة بناءً على الملاحظات)

    # ======================================================
    # Metadata
    # ======================================================

    @property
    def supported_environments(self) -> Tuple[EnvironmentType, ...]:
        return SUPPORTED_ENVIRONMENTS

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "current": self.name,
            "is_production": self.is_production,
            "is_development": self.is_development,
            "is_testing": self.is_testing,
            "is_staging": self.is_staging,
            "is_live": self.is_live,
            "is_local": self.is_local,
            "requires_strict_security": self.requires_strict_security,
            "supports_hot_reload": self.supports_hot_reload,
            "env_var_name": self.ENV_VAR_NAME
        }

    def __repr__(self) -> str:
        return f"<EnvironmentManager current='{self.name}'>"


# ==========================================================
# 2. Global Instance
# ==========================================================
environment = EnvironmentManager()

# ==========================================================
# 3. Explicit Public API
# ==========================================================
__all__ = [
    "EnvironmentManager",
    "environment",
]