"""
Integration Tests — المرحلة 2: خط أنابيب التسجيل

تختبر التدفق الحقيقي:
    LoggingManager.configure → تسجيل رسالة → قراءة الملف من القرص
"""

from __future__ import annotations

import logging

import pytest

from core.logging.log_filters import filter_factory
from core.logging.log_formatter import formatter_factory
from core.logging.log_handlers import handler_factory
from core.logging.logging_manager import LoggingManager


# ==========================================================
# Fixture: عزل كامل (root logger + Factories + Singleton)
# ==========================================================

@pytest.fixture
def clean_logging():
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level

    LoggingManager._instance = None
    yield

    # استعادة root logger
    root.handlers.clear()
    for h in saved_handlers:
        root.addHandler(h)
    root.setLevel(saved_level)

    # إيقاف الـ Manager وفك تجميد الـ Factories
    mgr = LoggingManager._instance
    if mgr is not None:
        try:
            mgr.shutdown()
        except Exception:
            pass

    for f in (formatter_factory, handler_factory, filter_factory):
        try:
            f.unfreeze()
            f.clear_cache()
        except Exception:
            pass

    LoggingManager._instance = None


# ==========================================================
# الاختبار: تسجيل حقيقي إلى ملف
# ==========================================================

def test_logging_end_to_end(clean_logging, tmp_path):
    # 1. تهيئة نظام التسجيل (staging → File Handler)
    manager = LoggingManager()
    manager.configure(
        environment="staging",
        log_level="INFO",
        log_dir=str(tmp_path),
    )
    assert manager.is_ready is True

    # 2. التسجيل عبر root logger مباشرة (حيث الـ File Handler مركّب)
    logging.getLogger().info("hello integration")

    # 3. تفريغ الـ Handlers إلى القرص
    for h in logging.getLogger().handlers:
        h.flush()

    # 4. التحقق أن الرسالة كُتبت فعلاً في الملف
    log_file = tmp_path / "halaliya.log"
    assert log_file.exists()
    assert "hello integration" in log_file.read_text(
        encoding="utf-8", errors="replace"
    )