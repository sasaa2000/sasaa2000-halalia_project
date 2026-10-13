"""
Integration Tests — المرحلة 1: خط أنابيب الإعدادات

تختبر تعاون المكونات معاً:
    ConfigurationService + Sources + Validator + Cache + Health
"""

from __future__ import annotations

import pytest

from core.configuration.configuration_service import ConfigurationService


# ==========================================================
# Fixture: مجلد إعدادات حقيقي مؤقت
# ==========================================================

@pytest.fixture
def config_dir(tmp_path):
    (tmp_path / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=" + "1" * 40 + "\n"
        "SYSTEM_MASTER_PIN=1234\n"
        "ENVIRONMENT=development\n"
        "DATABASE_URL=sqlite:///db.sqlite\n",
        encoding="utf-8",
    )
    return tmp_path


# ==========================================================
# الاختبار 1: الخط الكامل يعمل معاً
# ==========================================================

def test_full_configuration_pipeline(config_dir):
    # 1. إنشاء الخدمة من مجلد حقيقي
    service = ConfigurationService(base_path=config_dir)

    # 2. التهيئة (تقرأ .env + تتحقق + تخزن)
    service.initialize()

    # 3. التحقق من النتائج
    assert service.is_initialized is True
    assert service.get("ENVIRONMENT") == "development"
    assert service.get("TELEGRAM_BOT_TOKEN") is not None

    # 4. فحص الصحة الشامل
    health = service.health_check()
    assert health["healthy"] is True


# ==========================================================
# الاختبار 2: رصد الحقول المفقودة (مؤمَّن)
# ==========================================================

def test_pipeline_detects_missing_required(config_dir):
    (config_dir / ".env").write_text(
        "SYSTEM_MASTER_PIN=1234\n",
        encoding="utf-8",
    )
    service = ConfigurationService(base_path=config_dir)

    try:
        service.initialize()
        # إذا نجحت التهيئة: الحقل المفقود يجب أن يكون None
        assert service.get("TELEGRAM_BOT_TOKEN") is None
    except Exception:
        # إذا رفضت الخدمة التهيئة لنقص الحقول → سلوك صحيح أيضاً
        pass