"""
HALALIA Configuration Schema
Production Version 1.2.0 — VERIFIED

التحسين في v1.2.0:
    ✅ الاستيراد من configuration_models بدلاً من configuration_validator
       (يقضي على تكرار Enums ومشكلة تجاوز التحقق صمتاً)
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

# ✅ الاستيراد من المصدر الموحد للنماذج
from .configuration_models import (
    ValidationRule,
    ValidationRuleType,
    ValidationSeverity,
)


# ==========================================================
# Configuration Schema
# ==========================================================
class ConfigurationSchema:
    """مخطط الإعدادات الرئيسي — مستودع مركزي لقواعد التحقق"""

    SCHEMA_VERSION = "1.2.0"

    def __init__(self, name: str = "default"):
        self.name = name
        self._rules: Tuple[ValidationRule, ...] = ()
        self._custom_validators: Dict[str, Callable] = {}
        self._rule_counter = 0
        self._build_default_schema()

    def _next_rule_id(self) -> str:
        self._rule_counter += 1
        return f"{self.name.upper()}_RULE_{self._rule_counter:03d}"

    def _build_default_schema(self) -> None:
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="TELEGRAM_BOT_TOKEN",
            rule_type=ValidationRuleType.REQUIRED,
            message="توكن البوت مطلوب",
            severity=ValidationSeverity.CRITICAL,
        ))
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="TELEGRAM_BOT_TOKEN",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=40,
            message="توكن البوت قصير جداً (يجب أن يكون 40+ حرف)",
            severity=ValidationSeverity.CRITICAL,
        ))
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="SYSTEM_MASTER_PIN",
            rule_type=ValidationRuleType.REQUIRED,
            message="PIN الرئيسي مطلوب",
            severity=ValidationSeverity.ERROR,
        ))
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="SYSTEM_MASTER_PIN",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=4,
            message="PIN يجب أن يكون 4 أرقام على الأقل",
            severity=ValidationSeverity.ERROR,
        ))
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="ENVIRONMENT",
            rule_type=ValidationRuleType.CHOICE,
            value=("development", "staging", "production", "testing"),
            message="بيئة التشغيل غير صالحة",
            severity=ValidationSeverity.ERROR,
        ))
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="DATABASE_URL",
            rule_type=ValidationRuleType.REQUIRED,
            message="رابط قاعدة البيانات مطلوب",
            severity=ValidationSeverity.ERROR,
        ))
        self.add_rule(ValidationRule(
            id=self._next_rule_id(),
            field="OPENAI_API_KEY",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=10,
            message="مفتاح OpenAI API غير صالح",
            severity=ValidationSeverity.WARNING,
            optional=True,
        ))

    # ======================================================
    # Rule Management
    # ======================================================
    def add_rule(self, rule: ValidationRule) -> None:
        self._rules = self._rules + (rule,)

    def remove_rule(self, rule_id: str) -> bool:
        original_count = len(self._rules)
        self._rules = tuple(r for r in self._rules if r.id != rule_id)
        return len(self._rules) < original_count

    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        for rule in self._rules:
            if rule.id == rule_id:
                return rule
        return None

    # ======================================================
    # Query Interface
    # ======================================================
    def get_rules_for_field(self, field: str) -> Tuple[ValidationRule, ...]:
        return tuple(r for r in self._rules if r.field == field)

    def get_all_rules(self) -> Tuple[ValidationRule, ...]:
        return self._rules

    def has_field(self, field: str) -> bool:
        return any(r.field == field for r in self._rules)

    # ======================================================
    # Custom Validators
    # ======================================================
    def add_custom_validator(self, field: str, validator: Callable) -> None:
        self._custom_validators[field] = validator

    def get_custom_validator(self, field: str) -> Optional[Callable]:
        return self._custom_validators.get(field)

    def remove_custom_validator(self, field: str) -> bool:
        if field in self._custom_validators:
            del self._custom_validators[field]
            return True
        return False

    # ======================================================
    # Properties & Metadata
    # ======================================================
    @property
    def version(self) -> str:
        return self.SCHEMA_VERSION

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    @property
    def custom_validator_count(self) -> int:
        return len(self._custom_validators)

    @property
    def empty(self) -> bool:
        return self.rule_count == 0

    @property
    def initialized(self) -> bool:
        return self.rule_count > 0

    @property
    def fields(self) -> Tuple[str, ...]:
        return tuple(sorted({r.field for r in self._rules}))

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "rule_count": self.rule_count,
            "custom_validators": self.custom_validator_count,
            "fields": self.fields,
            "rules": [
                {
                    "id": r.id,
                    "field": r.field,
                    "type": r.rule_type.value,
                    "severity": r.severity.value,
                    "optional": r.optional,
                }
                for r in self._rules
            ],
        }

    def __repr__(self) -> str:
        return f"<ConfigurationSchema name='{self.name}' rules={self.rule_count}>"


# ==========================================================
# Global Default Instance
# ==========================================================
default_schema = ConfigurationSchema(name="halaliya_default")


__all__ = [
    "ConfigurationSchema",
    "default_schema",
]