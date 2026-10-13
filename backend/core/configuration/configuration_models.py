"""
HALALIA Configuration Models
Production Version 2.1.0 — VERIFIED

التحسين في v2.1.0:
    ✅ إضافة حقل statistics إلى ValidationReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, Optional


class SourcePriority(IntEnum):
    DEFAULT = 10
    FILE = 20
    DOTENV = 30
    ENVIRONMENT = 40
    RUNTIME = 50


MODEL_VERSION = "2.1.0"
__version__ = MODEL_VERSION


# ==========================================================
# 1. Core Enums
# ==========================================================

class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


SUPPORTED_ENVIRONMENTS = (
    EnvironmentType.DEVELOPMENT,
    EnvironmentType.STAGING,
    EnvironmentType.PRODUCTION,
    EnvironmentType.TESTING,
)


class ValidationRuleType(str, Enum):
    REQUIRED = "required"
    TYPE_CHECK = "type"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    RANGE = "range"
    PATTERN = "pattern"
    CHOICE = "choice"
    URL = "url"
    EMAIL = "email"
    CUSTOM = "custom"


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ==========================================================
# 2. Validation Data Models
# ==========================================================

@dataclass(slots=True, frozen=True)
class ValidationRule:
    id: str
    field: str
    rule_type: ValidationRuleType
    value: Any = None
    message: str = ""
    severity: ValidationSeverity = ValidationSeverity.ERROR
    optional: bool = False


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    severity: ValidationSeverity
    field: str
    rule_id: str
    message: str
    code: str

    @property
    def is_critical(self) -> bool:
        return self.severity == ValidationSeverity.CRITICAL


@dataclass(slots=True, frozen=True)
class ValidationStatistics:
    total_rules: int
    passed_rules: int
    failed_rules: int
    info_count: int
    warning_count: int
    error_count: int
    critical_count: int

    @property
    def coverage_percent(self) -> float:
        if self.total_rules == 0:
            return 100.0
        return (self.passed_rules / self.total_rules) * 100

    @property
    def failed(self) -> bool:
        return self.failed_rules > 0

    @property
    def passed(self) -> bool:
        return self.failed_rules == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "info_count": self.info_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "coverage_percent": round(self.coverage_percent, 2),
        }


@dataclass(slots=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)
    execution_time_ms: float = 0.0
    validated_fields: int = 0

    @property
    def is_valid(self) -> bool:
        return not any(
            i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            for i in self.issues
        )

    @property
    def has_critical(self) -> bool:
        return any(i.severity == ValidationSeverity.CRITICAL for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(
            i for i in self.issues
            if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        )

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def infos(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.INFO)

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": [
                {"field": i.field, "rule_id": i.rule_id, "message": i.message, "code": i.code}
                for i in self.errors
            ],
            "warnings": [
                {"field": i.field, "rule_id": i.rule_id, "message": i.message}
                for i in self.warnings
            ],
            "validated_fields": self.validated_fields,
            "execution_time_ms": self.execution_time_ms,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
        }


@dataclass(slots=True, frozen=True)
class ValidationReport:
    result: ValidationResult
    validated_at: str
    validator_version: str
    configuration_version: str
    environment: str
    schema_version: str = MODEL_VERSION
    statistics: Optional[ValidationStatistics] = None  # ✅ جديد

    @property
    def is_valid(self) -> bool:
        return self.result.is_valid

    @property
    def has_errors(self) -> bool:
        return not self.result.is_valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.result.is_valid,
            "environment": self.environment,
            "validator_version": self.validator_version,
            "configuration_version": self.configuration_version,
            "schema_version": self.schema_version,
            "validated_at": self.validated_at,
            "result": self.result.to_dict(),
            "statistics": self.statistics.to_dict() if self.statistics else None,  # ✅ جديد
        }


# ==========================================================
# 3. Explicit Public API
# ==========================================================
__all__ = [
    "MODEL_VERSION",
    "SourcePriority",
    "EnvironmentType",
    "SUPPORTED_ENVIRONMENTS",
    "ValidationRuleType",
    "ValidationSeverity",
    "ValidationRule",
    "ValidationIssue",
    "ValidationStatistics",
    "ValidationResult",
    "ValidationReport",
]