"""
اختبارات ConfigurationValidator — مطابقة للتنفيذ الفعلي.

ملاحظة جوهرية:
    ConfigurationSchema يبني 5 قواعد افتراضية تلقائياً.
    لذلك نستخدم BASE_CONFIG يُرضي هذه القواعد، ثم نضيف القاعدة قيد الاختبار.
"""

from __future__ import annotations

import pytest

from core.configuration.configuration_validator import (
    ConfigurationValidator,
    ConfigurationSchema,
    ValidationRule,
    ValidationRuleType,
    ValidationSeverity,
    ValidationStatistics,
)


# ==========================================================
# إعداد أساسي يُرضي القواعد الافتراضية الخمس
# ==========================================================

BASE_CONFIG = {
    "TELEGRAM_BOT_TOKEN": "1234567890" * 4,   # 40 حرفاً (REQUIRED + MIN_LENGTH 40)
    "SYSTEM_MASTER_PIN": "1234",               # REQUIRED
    "ENVIRONMENT": "development",              # CHOICE
    "DATABASE_URL": "postgresql://localhost/halaliya",  # REQUIRED
}


def _config(**extra):
    """دمج BASE_CONFIG مع حقول إضافية"""
    return {**BASE_CONFIG, **extra}


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def schema():
    """مخطط جديد لكل اختبار (يحتوي 5 قواعد افتراضية)"""
    return ConfigurationSchema()


@pytest.fixture
def validator(schema):
    return ConfigurationValidator(schema=schema)


# ==========================================================
# 1. ValidationRule Tests
# ==========================================================

class TestValidationRule:
    def test_create_rule(self):
        rule = ValidationRule(
            id="RULE_001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
            message="App name is required",
        )
        assert rule.id == "RULE_001"
        assert rule.field == "APP_NAME"
        assert rule.rule_type == ValidationRuleType.REQUIRED

    def test_rule_is_frozen(self):
        rule = ValidationRule(
            id="RULE_001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
        )
        with pytest.raises(AttributeError):
            rule.field = "MODIFIED"

    def test_rule_defaults(self):
        rule = ValidationRule(
            id="RULE_001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
        )
        assert rule.severity == ValidationSeverity.ERROR
        assert rule.optional is False
        assert rule.message == ""
        assert rule.value is None


# ==========================================================
# 2. Enums Tests
# ==========================================================

class TestValidationSeverity:
    def test_all_severities_exist(self):
        assert ValidationSeverity.INFO.value == "info"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.CRITICAL.value == "critical"


class TestValidationRuleType:
    def test_all_rule_types_exist(self):
        expected = {
            "required", "type", "min_length", "max_length",
            "min_value", "max_value", "range", "pattern",
            "choice", "url", "email", "custom",
        }
        actual = {rt.value for rt in ValidationRuleType}
        assert expected == actual


# ==========================================================
# 3. REQUIRED Rule
# ==========================================================

class TestRequiredRule:
    def test_required_passes_with_value(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True

    def test_required_fails_with_missing(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="MISSING_KEY",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.CRITICAL,
        ))
        report = validator.validate(_config())
        assert report.is_valid is False

    def test_required_fails_with_none(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="NULL_KEY",
            rule_type=ValidationRuleType.REQUIRED,
        ))
        report = validator.validate(_config(NULL_KEY=None))
        assert report.is_valid is False


# ==========================================================
# 4. TYPE_CHECK Rule
# ==========================================================

class TestTypeCheckRule:
    def test_type_check_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.TYPE_CHECK,
            value=int,
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is True

    def test_type_check_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.TYPE_CHECK,
            value=str,
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is False


# ==========================================================
# 5. MIN_LENGTH / MAX_LENGTH
# ==========================================================

class TestMinLengthRule:
    def test_min_length_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=3,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True

    def test_min_length_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=20,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is False


class TestMaxLengthRule:
    def test_max_length_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.MAX_LENGTH,
            value=20,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True

    def test_max_length_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.MAX_LENGTH,
            value=3,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is False


# ==========================================================
# 6. MIN_VALUE / MAX_VALUE
# ==========================================================

class TestMinValueRule:
    def test_min_value_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.MIN_VALUE,
            value=1024,
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is True

    def test_min_value_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.MIN_VALUE,
            value=9000,
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is False


class TestMaxValueRule:
    def test_max_value_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.MAX_VALUE,
            value=65535,
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is True

    def test_max_value_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.MAX_VALUE,
            value=1000,
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is False


# ==========================================================
# 7. RANGE / PATTERN / CHOICE
# ==========================================================

class TestRangeRule:
    def test_range_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.RANGE,
            value=(1, 65535),
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is True

    def test_range_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.RANGE,
            value=(9000, 10000),
        ))
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is False


class TestPatternRule:
    def test_pattern_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.PATTERN,
            value=r"^[A-Z]+$",
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True

    def test_pattern_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.PATTERN,
            value=r"^\d+$",
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is False


class TestChoiceRule:
    def test_choice_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="LOG_LEVEL",
            rule_type=ValidationRuleType.CHOICE,
            value=("DEBUG", "INFO", "WARNING", "ERROR"),
        ))
        report = validator.validate(_config(LOG_LEVEL="INFO"))
        assert report.is_valid is True

    def test_choice_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="LOG_LEVEL",
            rule_type=ValidationRuleType.CHOICE,
            value=("DEBUG", "WARNING", "ERROR"),
        ))
        report = validator.validate(_config(LOG_LEVEL="INFO"))
        assert report.is_valid is False


# ==========================================================
# 8. URL / EMAIL
# ==========================================================

class TestUrlRule:
    def test_url_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="WEBSITE",
            rule_type=ValidationRuleType.URL,
        ))
        report = validator.validate(_config(WEBSITE="https://halaliya.com"))
        assert report.is_valid is True

    def test_url_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="BAD_URL",
            rule_type=ValidationRuleType.URL,
        ))
        report = validator.validate(_config(BAD_URL="not-a-url"))
        assert report.is_valid is False


class TestEmailRule:
    def test_email_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="EMAIL",
            rule_type=ValidationRuleType.EMAIL,
        ))
        report = validator.validate(_config(EMAIL="admin@halaliya.com"))
        assert report.is_valid is True

    def test_email_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="BAD_EMAIL",
            rule_type=ValidationRuleType.EMAIL,
        ))
        report = validator.validate(_config(BAD_EMAIL="not-an-email"))
        assert report.is_valid is False


# ==========================================================
# 9. CUSTOM Rule
# ==========================================================

class TestCustomRule:
    def test_custom_validator_passes(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.CUSTOM,
        ))
        schema.add_custom_validator(
            "APP_PORT",
            lambda v: None if v > 0 else "Port must be positive"
        )
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is True

    def test_custom_validator_fails(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_PORT",
            rule_type=ValidationRuleType.CUSTOM,
        ))
        schema.add_custom_validator(
            "APP_PORT",
            lambda v: None if v > 9000 else "Port must be > 9000"
        )
        report = validator.validate(_config(APP_PORT=8080))
        assert report.is_valid is False


# ==========================================================
# 10. ValidationReport
# ==========================================================

class TestValidationReport:
    def test_report_is_valid(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True

    def test_report_to_dict_structure(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        result = report.to_dict()
        expected_keys = {
            "valid", "environment", "validator_version",
            "configuration_version", "schema_version",
            "validated_at", "result",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_report_has_errors_when_invalid(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="MISSING",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.CRITICAL,
        ))
        report = validator.validate(_config())
        assert report.is_valid is False
        assert report.result.has_critical is True


# ==========================================================
# 11. ValidationStatistics (مباشر — لا يعتمد على Schema)
# ==========================================================

class TestValidationStatistics:
    def test_statistics_coverage(self):
        stats = ValidationStatistics(
            total_rules=10, passed_rules=8, failed_rules=2,
            info_count=0, warning_count=1, error_count=1, critical_count=0,
        )
        assert stats.coverage_percent == 80.0

    def test_statistics_passed_failed(self):
        stats = ValidationStatistics(
            total_rules=5, passed_rules=5, failed_rules=0,
            info_count=0, warning_count=0, error_count=0, critical_count=0,
        )
        assert stats.passed is True
        assert stats.failed is False

    def test_statistics_zero_rules(self):
        stats = ValidationStatistics(
            total_rules=0, passed_rules=0, failed_rules=0,
            info_count=0, warning_count=0, error_count=0, critical_count=0,
        )
        assert stats.coverage_percent == 100.0


# ==========================================================
# 12. Multiple Rules
# ==========================================================

class TestMultipleRules:
    def test_multiple_rules_same_field(self, schema, validator):
        schema.add_rule(ValidationRule(id="R001", field="APP_NAME", rule_type=ValidationRuleType.REQUIRED))
        schema.add_rule(ValidationRule(id="R002", field="APP_NAME", rule_type=ValidationRuleType.MIN_LENGTH, value=3))
        schema.add_rule(ValidationRule(id="R003", field="APP_NAME", rule_type=ValidationRuleType.MAX_LENGTH, value=20))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True

    def test_one_failure_does_not_block_others(self, schema, validator):
        schema.add_rule(ValidationRule(id="R001", field="APP_NAME", rule_type=ValidationRuleType.MIN_LENGTH, value=100))
        schema.add_rule(ValidationRule(id="R002", field="APP_PORT", rule_type=ValidationRuleType.MIN_VALUE, value=1024))
        report = validator.validate(_config(APP_NAME="HALALIA", APP_PORT=8080))
        assert report.is_valid is False
        assert report.result.to_dict()["total_errors"] >= 1

    def test_all_rules_evaluated(self, schema, validator):
        for i in range(5):
            schema.add_rule(ValidationRule(
                id=f"R{i:03d}", field="APP_NAME",
                rule_type=ValidationRuleType.REQUIRED,
            ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True


# ==========================================================
# 13. Severity
# ==========================================================

class TestSeverity:
    def test_warning_does_not_make_invalid(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=100,
            severity=ValidationSeverity.WARNING,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is True
        assert report.result.has_warnings is True

    def test_error_makes_invalid(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=100,
            severity=ValidationSeverity.ERROR,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA"))
        assert report.is_valid is False


# ==========================================================
# 14. Optional Rules
# ==========================================================

class TestOptionalRules:
    def test_optional_rule_skips_missing(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="OPTIONAL_KEY",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=10,
            optional=True,
        ))
        report = validator.validate(_config())
        assert report.is_valid is True

    def test_optional_rule_validates_present(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="OPTIONAL_KEY",
            rule_type=ValidationRuleType.MIN_LENGTH,
            value=10,
            optional=True,
        ))
        report = validator.validate(_config(OPTIONAL_KEY="short"))
        assert report.is_valid is False


# ==========================================================
# 15. Edge Cases (مع القواعد الافتراضية)
# ==========================================================

class TestEdgeCases:
    def test_config_satisfying_defaults_is_valid(self, validator):
        """إعداد يُرضي القواعد الافتراضية → صالح"""
        report = validator.validate(BASE_CONFIG)
        assert report.is_valid is True

    def test_missing_default_required_is_invalid(self, validator):
        """حذف حقل مطلوب افتراضياً → غير صالح"""
        config = {k: v for k, v in BASE_CONFIG.items() if k != "TELEGRAM_BOT_TOKEN"}
        report = validator.validate(config)
        assert report.is_valid is False

    def test_config_with_extra_keys(self, schema, validator):
        schema.add_rule(ValidationRule(
            id="R001", field="APP_NAME",
            rule_type=ValidationRuleType.REQUIRED,
        ))
        report = validator.validate(_config(APP_NAME="HALALIA", EXTRA_KEY="extra"))
        assert report.is_valid is True


# ==========================================================
# 16. Schema (نسبي — بسبب القواعد الافتراضية)
# ==========================================================

class TestSchema:
    def test_schema_rule_count(self, schema):
        initial = schema.rule_count
        schema.add_rule(ValidationRule(
            id="R001", field="TEST",
            rule_type=ValidationRuleType.REQUIRED,
        ))
        assert schema.rule_count == initial + 1

    def test_schema_get_all_rules(self, schema):
        initial = len(schema.get_all_rules())
        schema.add_rule(ValidationRule(id="R001", field="A", rule_type=ValidationRuleType.REQUIRED))
        schema.add_rule(ValidationRule(id="R002", field="B", rule_type=ValidationRuleType.REQUIRED))
        rules = schema.get_all_rules()
        assert len(rules) == initial + 2

    def test_schema_custom_validator(self, schema):
        validator_fn = lambda v: None
        schema.add_custom_validator("TEST_FIELD", validator_fn)
        assert schema.get_custom_validator("TEST_FIELD") is validator_fn
        assert schema.get_custom_validator("NONEXISTENT") is None


# ==========================================================
# 17. Validator Version
# ==========================================================

class TestValidatorVersion:
    def test_validator_version(self, validator):
        assert validator.version is not None
        assert isinstance(validator.version, str)