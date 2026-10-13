"""
HALALIA Test Configuration — v1.1
✅ يستخدم reset() و reset_instance() بدلاً من لمس المتغيرات الخاصة.
"""

from __future__ import annotations

import pytest

from core.monitoring.metrics import (
    MetricRegistry,
    MetricsService,
)


@pytest.fixture(autouse=True)
def reset_metrics():
    """إعادة تعيين Metrics قبل وبعد كل اختبار"""
    # ✅ استخدام API العام بدلاً من _metrics
    MetricRegistry.reset_instance()
    MetricsService.reset_instance()

    yield

    # تنظيف بعد الاختبار
    MetricRegistry.reset_instance()
    MetricsService.reset_instance()


@pytest.fixture
def fresh_registry():
    """Registry جديد تماماً"""
    MetricRegistry.reset_instance()
    return MetricRegistry()


@pytest.fixture
def fresh_service():
    """MetricsService جديد تماماً"""
    MetricsService.reset_instance()
    return MetricsService()