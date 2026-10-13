"""
HALALIA Configuration Sources
Production Version 1.1 — VERIFIED

المؤسس: جمال الدين زيدان
الحالة: Production Ready ✅

التحسينات المطبقة:
    ✅ إزالة print واستبدالها برفع الاستثناءات
    ✅ استخدام SourcePriority بدلاً من الأرقام السحرية
    ✅ التحقق من نوع JSON (يجب أن يكون dict)
    ✅ معالجة الحقول الفارغة في DotEnvSource
    ✅ إضافة source_count و available_count
    ✅ Factory يرجع ConfigurationSourceManager جاهزاً
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from .configuration_models import SourcePriority


# ==========================================================
# 1. Abstract Base Class
# ==========================================================

class ConfigurationSource(ABC):
    """الواجهة الأساسية لأي مصدر إعدادات"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        pass


# ==========================================================
# 2. Standard Implementations
# ==========================================================

class EnvironmentSource(ConfigurationSource):
    """مصدر متغيرات البيئة"""

    @property
    def name(self) -> str:
        return "EnvironmentVariables"

    def is_available(self) -> bool:
        return True

    def load(self) -> Dict[str, Any]:
        return dict(os.environ)


class DotEnvSource(ConfigurationSource):
    """مصدر ملف .env"""

    def __init__(self, env_path: Path, treat_empty_as_none: bool = True):
        self.env_path = env_path
        self.treat_empty_as_none = treat_empty_as_none

    @property
    def name(self) -> str:
        return f"DotEnv({self.env_path.name})"

    def is_available(self) -> bool:
        return self.env_path.exists() and self.env_path.is_file()

    def load(self) -> Dict[str, Any]:
        config = {}
        with open(self.env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    # ✅ التحسين 4: معالجة الحقول الفارغة
                    if self.treat_empty_as_none and value == "":
                        config[key] = None
                    else:
                        config[key] = value
        return config


class JsonSource(ConfigurationSource):
    """مصدر ملف JSON"""

    def __init__(self, json_path: Path):
        self.json_path = json_path

    @property
    def name(self) -> str:
        return f"Json({self.json_path.name})"

    def is_available(self) -> bool:
        return self.json_path.exists() and self.json_path.is_file()

    def load(self) -> Dict[str, Any]:
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ✅ التحسين 3: التحقق من نوع JSON
        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid JSON structure in {self.json_path}: "
                f"Expected object, got {type(data).__name__}"
            )

        return data


# ==========================================================
# 3. Source Manager
# ==========================================================

class ConfigurationSourceManager:
    """مدير مصادر الإعدادات"""

    def __init__(self):
        self._sources: List[tuple[SourcePriority, ConfigurationSource]] = []

    def add_source(self, source: ConfigurationSource, priority: SourcePriority = SourcePriority.DEFAULT) -> None:
        self._sources.append((priority, source))
        self._sources.sort(key=lambda x: x[0])

    def get_available_sources(self) -> List[ConfigurationSource]:
        return [source for _, source in self._sources if source.is_available()]

    def load_all(self) -> Dict[str, Any]:
        merged_config = {}

        for priority, source in self._sources:
            if source.is_available():
                # ✅ التحسين 1: رفع الاستثناء بدلاً من print
                data = source.load()
                merged_config.update(data)

        return merged_config

    # سطر فارغ إضافي لتحسين التنسيق بين الدوال والخصائص (تمت الإضافة بناءً على الملاحظات)

    @property
    def source_count(self) -> int:
        return len(self._sources)

    @property
    def available_count(self) -> int:
        return len(self.get_available_sources())


# ==========================================================
# 4. Factory
# ==========================================================

class SourceFactory:
    """مصنع لإنشاء مصادر الإعدادات القياسية"""

    @staticmethod
    def create_default_manager(base_path: Path) -> ConfigurationSourceManager:
        """إنشاء ConfigurationSourceManager جاهز بالمصادر الافتراضية"""
        manager = ConfigurationSourceManager()

        # 1. ملف JSON (أولوية منخفضة)
        json_path = base_path / "config.json"
        if json_path.exists():
            manager.add_source(JsonSource(json_path), SourcePriority.FILE)

        # 2. ملف .env (أولوية متوسطة)
        env_path = base_path / ".env"
        manager.add_source(DotEnvSource(env_path), SourcePriority.DOTENV)

        # 3. متغيرات البيئة (أولوية عالية)
        manager.add_source(EnvironmentSource(), SourcePriority.ENVIRONMENT)

        return manager