"""
HALALIA Configuration Profiles
Production Version 1.1 — VERIFIED

المؤسس: جمال الدين زيدان
الحالة: Production Ready ✅

التحسينات المطبقة:
    ✅ إزالة جميع الأسرار (Secrets) مثل DATABASE_URL من الـ Profiles.
    ✅ توحيد أسماء المفاتيح بالبادئة APP_ (APP_DEBUG, APP_LOG_LEVEL, etc.).
    ✅ إضافة properties و methods جديدة (profiles, names, has_profile, remove_profile).
    ✅ حماية الـ Active Profile من الحذف العرضي.
    ✅ إضافة ملاحظات معمارية (TODO) لـ deep_merge و Strong Typing مستقبلاً.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .configuration_models import EnvironmentType


# ==========================================================
# 1. Configuration Profile
# ==========================================================

class ConfigurationProfile:
    """ملف شخصي واحد للإعدادات (يحمل سلوك البيئة فقط، بدون أسرار)"""

    def __init__(
            self,
            name: str,
            environment: EnvironmentType,
            overrides: Dict[str, Any]
    ):
        self.name = name
        self.environment = environment
        self.overrides = overrides

    def apply_to(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        تطبيق overrides على الإعدادات.
        ملاحظة معمارية: هذا دمج سطحي (Shallow Merge).
        TODO: في المستقبل، استبدل هذا باستدعاء deep_merge() من configuration_utils.py
        لدعم القواميس المتداخلة (Nested Dicts) بشكل آمن.
        """
        merged = config.copy()
        merged.update(self.overrides)
        return merged

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "environment": self.environment.value,
            "overrides": self.overrides
        }


# ==========================================================
# 2. Profile Manager
# ==========================================================

class ProfileManager:
    """مدير الملفات الشخصية للبيئات المختلفة"""

    def __init__(self):
        self._profiles: Dict[str, ConfigurationProfile] = {}
        self._active_profile: Optional[str] = None
        self._load_default_profiles()

    def _load_default_profiles(self) -> None:
        """تحميل الملفات الشخصية الافتراضية (بدون أي Secrets)"""

        # Development Profile
        self.add_profile(ConfigurationProfile(
            name="development",
            environment=EnvironmentType.DEVELOPMENT,
            overrides={
                "APP_DEBUG": True,
                "APP_LOG_LEVEL": "DEBUG",
                "APP_CACHE_ENABLED": False,
                "APP_METRICS_ENABLED": False,
                "APP_TRACING_ENABLED": True
            }
        ))

        # Testing Profile
        self.add_profile(ConfigurationProfile(
            name="testing",
            environment=EnvironmentType.TESTING,
            overrides={
                "APP_DEBUG": True,
                "APP_LOG_LEVEL": "WARNING",
                "APP_CACHE_ENABLED": False,
                "APP_METRICS_ENABLED": True,
                "APP_TRACING_ENABLED": False
            }
        ))

        # Staging Profile
        self.add_profile(ConfigurationProfile(
            name="staging",
            environment=EnvironmentType.STAGING,
            overrides={
                "APP_DEBUG": False,
                "APP_LOG_LEVEL": "INFO",
                "APP_CACHE_ENABLED": True,
                "APP_METRICS_ENABLED": True,
                "APP_TRACING_ENABLED": True
            }
        ))

        # Production Profile
        self.add_profile(ConfigurationProfile(
            name="production",
            environment=EnvironmentType.PRODUCTION,
            overrides={
                "APP_DEBUG": False,
                "APP_LOG_LEVEL": "ERROR",
                "APP_CACHE_ENABLED": True,
                "APP_METRICS_ENABLED": True,
                "APP_TRACING_ENABLED": True
            }
        ))

        # سطر فارغ إضافي لتحسين التنسيق (تمت الإضافة بناءً على الملاحظات)

    def add_profile(self, profile: ConfigurationProfile) -> None:
        """إضافة ملف شخصي جديد"""
        self._profiles[profile.name] = profile

    def get_profile(self, name: str) -> Optional[ConfigurationProfile]:
        """الحصول على ملف شخصي بالاسم"""
        return self._profiles.get(name)

    def set_active_profile(self, name: str) -> None:
        """تعيين الملف الشخصي النشط"""
        if not self.has_profile(name):
            raise ValueError(f"Profile '{name}' not found")
        self._active_profile = name

    def get_active_profile(self) -> Optional[ConfigurationProfile]:
        """الحصول على الملف الشخصي النشط حالياً"""
        if self._active_profile:
            return self._profiles.get(self._active_profile)
        return None

    def apply_active_profile(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """تطبيق إعدادات الملف النشط على القاموس الممرر"""
        profile = self.get_active_profile()
        if profile:
            return profile.apply_to(config)
        return config

    def has_profile(self, name: str) -> bool:
        """التحقق من وجود ملف شخصي بالاسم"""
        return name in self._profiles

    def remove_profile(self, name: str) -> None:
        """حذف ملف شخصي (مع حماية الملف النشط)"""
        if name == self._active_profile:
            raise RuntimeError("Cannot remove the currently active profile.")

        self._profiles.pop(name, None)

    # ======================================================
    # Properties & Metadata
    # ======================================================

    @property
    def profile_count(self) -> int:
        return len(self._profiles)

    @property
    def active_profile_name(self) -> Optional[str]:
        return self._active_profile

    @property
    def profiles(self) -> Tuple[ConfigurationProfile, ...]:
        """إرجاع جميع الملفات الشخصية كـ Tuple (غير قابل للتعديل)"""
        return tuple(self._profiles.values())

    @property
    def names(self) -> Tuple[str, ...]:
        """إرجاع أسماء جميع الملفات الشخصية كـ Tuple"""
        return tuple(self._profiles.keys())