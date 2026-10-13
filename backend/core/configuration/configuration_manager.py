"""
HALALIA Configuration Manager
Production Version 3.0 (Final Unified Edition)

المؤسس:
    جمال الدين زيدان

Architecture Review:
    OpenAI Production Refactoring & Co-Creation

الوصف:
    المدير المركزي والآمن لجميع إعدادات HALALIA.
    هذه النسخة تجمع أفضل ما في كل الإصدارات السابقة:
    - تغليف كامل (Encapsulation) عبر Properties بدل Attributes مباشرة
    - حماية Runtime بقائمة بيضاء صريحة (Whitelist)
    - دعم Reload و Health Check للمراقبة والصيانة الحية
    - Metadata و Profiles قابلة للتوسع
    - Secret Hooks جاهزة للترحيل لـ Secret Manager مستقبلاً

المسؤوليات:
    - تحميل الإعدادات بشكل آمن ومتعدد المصادر
    - إدارة حالة النظام (State Management)
    - توفير Singleton آمن للخيوط (Thread-Safe)
    - الحفاظ على Backward Compatibility
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# ==========================================================
# Resilient Logging Fallback
# ==========================================================
try:
    from core.logger import system_logger, error_logger
except Exception:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    system_logger = logging.getLogger("HALALIA_CONFIGURATION")
    error_logger = logging.getLogger("HALALIA_CONFIGURATION_ERROR")


# ==========================================================
# Project Root Resolution
# ==========================================================
# يضمن العثور على المجلد الجذري بغض النظر عن مكان استدعاء هذا الملف
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# تحميل متغيرات البيئة مبكراً
load_dotenv(ENV_PATH)


# ==========================================================
# Configuration Manager (Thread-Safe Singleton)
# ==========================================================
class ConfigurationManager:
    """
    Production Configuration Manager
    Singleton | Thread Safe | State Aware
    """

    _instance: Optional["ConfigurationManager"] = None
    _lock = threading.Lock()
    _initialized = False

    # قائمة بيضاء بالمفاتيح المسموح بتعديلها أثناء التشغيل فقط
    _ALLOWED_RUNTIME_KEYS = {"MAINTENANCE_MODE", "DEBUG_MODE"}

    def __new__(cls) -> "ConfigurationManager":
        # Double-checked locking pattern لأمان تعدد الخيوط
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):

        if self.__class__._initialized:
            return

        self.__class__._initialized = True

        # تهيئة القواميس الأساسية
        self._config: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._profiles: Dict[str, Any] = {}

        self._state = "LOADING"
        self._sealed = False

        system_logger.info("🔄 Loading HALALIA Configuration...")

        try:
            self._load_configurations()
            self._state = "READY"
            system_logger.info("✅ HALALIA Configuration Loaded Successfully.")
        except Exception as exc:
            self._state = "FAILED"
            error_logger.exception(f"❌ Failed to load configuration: {exc}")
            # نوقف التطبيق فوراً إذا فشلت الإعدادات الأساسية (مثل غياب Bot Token)
            # لأن الاستمرار بدون التوكن سيؤدي لأخطاء غير متوقعة لاحقاً.
            raise RuntimeError("Configuration initialization failed") from exc

    # ======================================================
    # State Management Properties
    # ======================================================
    @property
    def state(self) -> str:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._state == "READY"

    @property
    def is_failed(self) -> bool:
        return self._state == "FAILED"

    @property
    def loaded(self) -> bool:
        """هل تم تحميل الإعدادات بنجاح؟"""
        return self.state == "READY"

    @property
    def failed(self) -> bool:
        """هل فشل تحميل الإعدادات؟"""
        return self.state == "FAILED"

    @property
    def initialized(self) -> bool:
        """هل تم تهيئة الـ Singleton من قبل؟"""
        return self.__class__._initialized

    @property
    def count(self) -> int:
        """عدد الإعدادات المحملة."""
        return len(self._config)

    @property
    def sealed(self) -> bool:
        """
        هل تم إغلاق الإعدادات؟
        بعد انتهاء التحميل تصبح جميع الإعدادات الأساسية للقراءة فقط،
        فيما عدا المفاتيح المدرجة صراحة في _ALLOWED_RUNTIME_KEYS.
        """
        return self._sealed

    # ======================================================
    # Internal Helpers
    # ======================================================
    def _set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def _get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    # ======================================================
    # Type Helpers
    # ======================================================
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """
        قراءة قيمة Boolean من Environment بطريقة آمنة.
        """
        value = os.getenv(key)
        if value is None:
            return default

        return value.strip().lower() in {
            "1", "true", "yes", "on", "enabled"
        }

    def _get_string(self, key: str, default: str = "") -> str:
        """
        قراءة قيمة String مع توفير قيمة افتراضية.
        """
        value = os.getenv(key)
        if value is None:
            return default
        return value.strip()

    def _require(self, key: str) -> str:
        """
        قراءة قيمة إلزامية (Required). ترفع خطأ إذا لم تكن موجودة.
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Missing required environment variable: {key}")
        return value.strip()

    # ======================================================
    # Configuration Loader
    # ======================================================
    def _load_configurations(self) -> None:
        """
        تحميل جميع إعدادات HALALIA.

        قاعدة معمارية صارمة:
        هذه الدالة هي المكان الوحيد المسموح فيه بقراءة Environment Variables.
        لا يسمح لأي جزء آخر في النظام باستخدام os.getenv() مباشرة.
        """
        system_logger.debug("Starting to load environment variables...")

        # --------------------------------------------------
        # 1. Telegram (إلزامي)
        # --------------------------------------------------
        self._set("TELEGRAM_BOT_TOKEN", self._require("TELEGRAM_BOT_TOKEN"))
        self._set("ADMIN_CHAT_ID", self._get_string("ADMIN_CHAT_ID", ""))

        # --------------------------------------------------
        # 2. Security
        # --------------------------------------------------
        self._set("SYSTEM_MASTER_PIN", self._get_string("SYSTEM_MASTER_PIN", "1234"))

        # --------------------------------------------------
        # 3. AI Providers
        # --------------------------------------------------
        self._set("OPENAI_API_KEY", self._get_string("OPENAI_API_KEY", ""))
        self._set("GOOGLE_VISION_API_KEY", self._get_string("GOOGLE_VISION_API_KEY", ""))
        self._set("GTTS_LANGUAGE", self._get_string("GTTS_LANGUAGE", "ar"))

        # --------------------------------------------------
        # 4. Database
        # --------------------------------------------------
        self._set("DATABASE_URL", self._get_string("DATABASE_URL", "sqlite:///halaliya_local.db"))

        # --------------------------------------------------
        # 5. Automation (n8n)
        # --------------------------------------------------
        self._set("N8N_WEBHOOK_URL", self._get_string("N8N_WEBHOOK_URL", ""))

        # --------------------------------------------------
        # 6. Feature Flags
        # --------------------------------------------------
        self._set("ENABLE_VOICE_RESPONSE", self._get_bool("ENABLE_VOICE_RESPONSE", True))
        self._set("ENABLE_IMAGE_SEARCH", self._get_bool("ENABLE_IMAGE_SEARCH", True))
        self._set("MAINTENANCE_MODE", self._get_bool("MAINTENANCE_MODE", False))

        # --------------------------------------------------
        # 7. Environment & App Version
        # --------------------------------------------------
        env = self._get_string("ENVIRONMENT", "development").lower()
        self._set("ENVIRONMENT", env)
        self._set("DEBUG_MODE", self._get_bool("DEBUG", False))
        self._set("APP_VERSION", self._get_string("APP_VERSION", "3.0.0"))

        system_logger.info(f"✅ HALALIA Configuration Loaded. Running Environment: {env}")

        # --------------------------------------------------
        # 8. Seal the Configuration (إغلاق الإعدادات)
        # --------------------------------------------------
        self._sealed = True
        system_logger.info("🔒 Configuration has been sealed. Runtime modifications are now restricted.")

    # ======================================================
    # Reload (للتطوير والصيانة الحية)
    # ======================================================
    def reload(self) -> None:
        """
        إعادة تحميل الإعدادات من ملف .env ومن Environment.

        تُستخدم فقط أثناء التطوير أو الصيانة، أو عند تفعيل
        Hot-Reload في بيئة الإنتاج بحرص شديد.
        لا تمسح Metadata أو Profiles المسجّلة يدوياً في وقت التشغيل.
        """
        system_logger.info("🔄 Reloading configuration...")

        self._sealed = False
        self._state = "LOADING"

        load_dotenv(ENV_PATH, override=True)

        self._config.clear()

        try:
            self._load_configurations()
            self._state = "READY"
            system_logger.info("✅ Configuration reloaded successfully.")
        except Exception as exc:
            self._state = "FAILED"
            error_logger.exception(f"❌ Failed to reload configuration: {exc}")
            raise RuntimeError("Configuration reload failed") from exc

    # ======================================================
    # Health Check
    # ======================================================
    def health_check(self) -> Dict[str, Any]:
        """
        فحص سريع لحالة مدير الإعدادات، مناسب لربطه بـ endpoint مراقبة (/health).
        """
        return {
            "version": self.app_version,
            "ready": self.is_ready,
            "sealed": self.sealed,
            "environment": self.environment,
            "configuration_count": self.count,
            "status": self.state,
        }

    # ======================================================
    # Public Properties (Clean Access API)
    # ======================================================
    # هذه الخصائص هي الطريقة المفضّلة لباقي النظام
    # للوصول إلى الإعدادات دون كسر قاعدة التغليف (Encapsulation)

    @property
    def bot_token(self) -> str:
        return self._get("TELEGRAM_BOT_TOKEN")

    @property
    def admin_chat_id(self) -> Optional[str]:
        return self._get("ADMIN_CHAT_ID")

    @property
    def is_debug(self) -> bool:
        return self._get("DEBUG_MODE", False)

    @property
    def is_voice_enabled(self) -> bool:
        return self._get("ENABLE_VOICE_RESPONSE", False)

    @property
    def is_image_search_enabled(self) -> bool:
        return self._get("ENABLE_IMAGE_SEARCH", False)

    @property
    def is_maintenance_mode(self) -> bool:
        return self._get("MAINTENANCE_MODE", False)

    @property
    def app_version(self) -> str:
        return self._get("APP_VERSION", "3.0.0")

    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """
        الحصول على حالة ميزة معينة بشكل آمن، مثال: get_feature_flag('voice').

        يبحث عن المفتاح بصيغتين لأن بعض الأعلام مخزّنة بلاحقة إضافية
        (مثال: ENABLE_VOICE_RESPONSE بدلاً من ENABLE_VOICE فقط).
        """
        base_key = f"ENABLE_{flag_name.upper()}"
        for key in (base_key, f"{base_key}_RESPONSE"):
            if key in self._config:
                return self._config[key]
        return default

    # ======================================================
    # Runtime Information (Environment)
    # ======================================================
    @property
    def environment(self) -> str:
        return self._get("ENVIRONMENT", "development")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

    # ======================================================
    # Public Configuration API
    # ======================================================
    def get(self, key: str, default: Any = None) -> Any:
        """
        القراءة العامة من Configuration Store.
        قاعدة: لا تستخدم os.getenv خارج هذا الملف.
        """
        return self._config.get(key, default)

    def exists(self, key: str) -> bool:
        """التحقق من وجود إعداد معين."""
        return key in self._config

    def keys(self) -> tuple:
        """إرجاع جميع أسماء الإعدادات كـ Tuple (غير قابلة للتعديل)."""
        return tuple(self._config.keys())

    def as_dict(self) -> Dict[str, Any]:
        """إرجاع نسخة للقراءة فقط من جميع الإعدادات."""
        return dict(self._config)

    # ======================================================
    # Runtime Protection (Immutability)
    # ======================================================
    def set_runtime(self, key: str, value: Any) -> None:
        """
        يسمح بتعديل قيم Runtime المحددة فقط (Whitelist).
        يحمي Secrets و Environment من التعديل العرضي.
        """
        if key not in self._ALLOWED_RUNTIME_KEYS:
            raise PermissionError(
                f"Modification of '{key}' is not allowed at runtime. "
                f"Only {sorted(self._ALLOWED_RUNTIME_KEYS)} can be modified."
            )

        self._config[key] = value
        system_logger.info(f"⚙️ Runtime configuration updated: {key} = {value}")

    def validate(self) -> bool:
        """
        Validation Hook
        سيتم ربطه مستقبلاً مع Configuration Validator للتحقق العميق.
        """
        # TODO: استدعاء ConfigurationValidator هنا في Package 3/8
        return True

    # ======================================================
    # Secret Hooks (Future-Proofing)
    # ======================================================
    def has_secret(self, key: str) -> bool:
        """التحقق من وجود قيمة لسر معين."""
        return bool(self._config.get(key))

    def get_secret(self, key: str) -> Optional[str]:
        """
        مؤقتاً يتم القراءة من Configuration.
        لاحقاً سيتم تحويلها لاستدعاء Secret Manager خارجي.
        """
        if self.is_production and key in ("TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY"):
            system_logger.warning(
                f"Accessing secret '{key}' directly. Consider migrating to Secret Manager."
            )
        return self._config.get(key, "")

    # ======================================================
    # Metadata Management
    # ======================================================
    def set_metadata(self, key: str, value: Any) -> None:
        """تسجيل بيانات وصفية إضافية حول الإعدادات."""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """قراءة البيانات الوصفية."""
        return self._metadata.get(key, default)

    # ======================================================
    # Profiles Management
    # ======================================================
    def register_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> None:
        """تسجيل ملف شخصي (Profile) جديد للإعدادات."""
        self._profiles[profile_name] = profile_data
        system_logger.debug(f"Registered configuration profile: {profile_name}")

    def profile_exists(self, profile_name: str) -> bool:
        """التحقق من وجود ملف شخصي معين."""
        return profile_name in self._profiles

    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        """الحصول على بيانات ملف شخصي معين."""
        return self._profiles.get(profile_name, {})

    # ======================================================
    # Path Properties (معلومات المسارات)
    # ======================================================
    @property
    def project_root(self) -> Path:
        """المسار الجذري للمشروع."""
        return BASE_DIR

    @property
    def env_file(self) -> Path:
        """مسار ملف .env."""
        return ENV_PATH

    # ======================================================
    # Settings Summary
    # ======================================================
    def get_all_settings_summary(self) -> Dict[str, Any]:
        """ملخص آمن للإعدادات (بدون بيانات حساسة) للتشخيص."""
        return {
            "environment": self.environment,
            "state": self.state,
            "version": self.app_version,
            "sealed": self.sealed,
            "configuration_count": len(self._config),

            "profiles": len(self._profiles),
            "metadata": len(self._metadata),

            "telegram": {
                "bot_token_set": bool(self._get("TELEGRAM_BOT_TOKEN")),
                "admin_chat_set": bool(self._get("ADMIN_CHAT_ID")),
            },

            "providers": {
                "openai_set": bool(self._get("OPENAI_API_KEY")),
                "google_vision_set": bool(self._get("GOOGLE_VISION_API_KEY")),
            },

            "database": {
                "configured": bool(self._get("DATABASE_URL")),
            },

            "features": {
                "voice": self._get("ENABLE_VOICE_RESPONSE", False),
                "image_search": self._get("ENABLE_IMAGE_SEARCH", False),
                "maintenance": self._get("MAINTENANCE_MODE", False),
            }
        }


# ==========================================================
# Global Instance Export
# ==========================================================
# يتم إنشاء النسخة عند أول استيراد لهذا الملف
system_logger.info(
    "HALALIA Configuration Manager initialized."
)

config = ConfigurationManager()