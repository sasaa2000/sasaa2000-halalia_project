"""
اختبارات الوحدة لنظام العدادات — v1.2 (كاملة ونظيفة)
"""

from __future__ import annotations

import threading
import time

import pytest

from core.monitoring.metrics import (
    METRICS_VERSION,
    ConsoleExporter,
    Counter,
    Gauge,
    Histogram,
    MetricNotFoundError,
    MetricRegistrationError,
    MetricRegistry,
    MetricType,
    MetricsService,
    PrometheusExporter,
    Summary,
    Timer,
    metrics_service,
)


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def fresh_registry():
    MetricRegistry.reset_instance()
    registry = MetricRegistry()
    yield registry
    MetricRegistry.reset_instance()


@pytest.fixture
def fresh_service():
    MetricsService.reset_instance()
    MetricRegistry.reset_instance()
    service = MetricsService()
    yield service
    MetricsService.reset_instance()
    MetricRegistry.reset_instance()


# ==========================================================
# 1. Counter
# ==========================================================

class TestCounter:
    def test_create_counter(self):
        counter = Counter("test_counter", "Test description")
        assert counter.name == "test_counter"
        assert counter.description == "Test description"
        assert counter.metric_type == MetricType.COUNTER

    def test_increment_default(self):
        counter = Counter("c")
        counter.inc()
        counter.inc()
        assert counter.get() == 2.0

    def test_increment_custom_amount(self):
        counter = Counter("c")
        counter.inc(5)
        counter.inc(3.5)
        assert counter.get() == 8.5

    def test_increment_negative_raises(self):
        counter = Counter("c")
        with pytest.raises(ValueError, match="non-negative"):
            counter.inc(-1)

    def test_counter_with_labels(self):
        counter = Counter("http_requests", labels=("method", "status"))
        counter.inc(method="GET", status="200")
        counter.inc(method="POST", status="201")
        counter.inc(method="GET", status="200")
        assert counter.get(method="GET", status="200") == 2.0
        assert counter.get(method="POST", status="201") == 1.0
        assert counter.get(method="GET", status="404") == 0.0

    def test_counter_collect_structure(self):
        counter = Counter("c")
        counter.inc(5)
        collected = counter.collect()
        assert collected["type"] == "counter"
        assert collected["total"] == 5.0

    def test_counter_invalid_name(self):
        with pytest.raises(MetricRegistrationError):
            Counter("", "description")
        with pytest.raises(MetricRegistrationError):
            Counter(None, "description")


# ==========================================================
# 2. Gauge
# ==========================================================

class TestGauge:
    def test_create_gauge(self):
        assert Gauge("memory_usage", "Memory in MB").metric_type == MetricType.GAUGE

    def test_set_value(self):
        gauge = Gauge("g")
        gauge.set(42.5)
        assert gauge.get() == 42.5

    def test_increment_and_decrement(self):
        gauge = Gauge("g")
        gauge.set(10)
        gauge.inc()
        gauge.inc(5)
        gauge.dec()
        gauge.dec(3)
        assert gauge.get() == 12.0

    def test_gauge_with_labels(self):
        gauge = Gauge("cpu", labels=("core",))
        gauge.set(75.0, core="0")
        gauge.set(50.0, core="1")
        assert gauge.get(core="0") == 75.0
        assert gauge.get(core="1") == 50.0

    def test_gauge_can_go_negative(self):
        gauge = Gauge("g")
        gauge.set(-10.5)
        assert gauge.get() == -10.5


# ==========================================================
# 3. Histogram
# ==========================================================

class TestHistogram:
    def test_create_histogram(self):
        assert Histogram("request_duration").metric_type == MetricType.HISTOGRAM

    def test_observe_increments_count(self):
        h = Histogram("h")
        h.observe(0.5)
        h.observe(1.5)
        h.observe(2.5)
        data = list(h.collect()["data"].values())[0]
        assert data["count"] == 3

    def test_observe_tracks_sum(self):
        h = Histogram("h")
        h.observe(1.0)
        h.observe(2.0)
        h.observe(3.0)
        data = list(h.collect()["data"].values())[0]
        assert data["sum"] == 6.0

    def test_histogram_bucket_count(self):
        h = Histogram("h", buckets=(0.1, 0.5, 1.0))
        h.observe(0.05)
        assert len(h.collect()["buckets"]) == 3


# ==========================================================
# 4. Summary
# ==========================================================

class TestSummary:
    def test_create_summary(self):
        assert Summary("response_time").metric_type == MetricType.SUMMARY

    def test_observe_tracks_count_and_sum(self):
        s = Summary("s")
        for i in range(100):
            s.observe(float(i))
        data = list(s.collect()["data"].values())[0]
        assert data["count"] == 100
        assert data["sum"] == sum(range(100))

    def test_summary_quantiles_reasonable(self):
        s = Summary("s", quantiles=(0.5, 0.9))
        for i in range(100):
            s.observe(float(i))
        quantiles = list(s.collect()["data"].values())[0]["quantiles"]
        assert 0 <= quantiles["q0.5"] <= 60
        assert 80 <= quantiles["q0.9"] <= 100


# ==========================================================
# 5. Timer
# ==========================================================

class TestTimer:
    def test_timer_measures_duration(self, monkeypatch):
        call_count = [0]
        monkeypatch.setattr(time, "perf_counter", lambda: call_count.__setitem__(0, call_count[0] + 1) or call_count[0] * 0.1)
        with Timer(Histogram("h")) as t:
            pass
        assert t.duration == pytest.approx(0.1, abs=0.01)

    def test_timer_records_to_histogram(self, monkeypatch):
        call_count = [0]
        monkeypatch.setattr(time, "perf_counter", lambda: call_count.__setitem__(0, call_count[0] + 1) or call_count[0] * 0.05)
        h = Histogram("h")
        with Timer(h):
            pass
        data = list(h.collect()["data"].values())[0]
        assert data["count"] == 1

    def test_timer_with_labels(self, monkeypatch):
        call_count = [0]
        monkeypatch.setattr(time, "perf_counter", lambda: call_count.__setitem__(0, call_count[0] + 1) or call_count[0] * 0.01)
        h = Histogram("h", labels=("endpoint",))
        with Timer(h, endpoint="/api/users"):
            pass
        assert "('/api/users',)" in h.collect()["data"]


# ==========================================================
# 6. MetricRegistry
# ==========================================================

class TestMetricRegistry:
    def test_register_counter(self, fresh_registry):
        counter = fresh_registry.get_or_create_counter("test_counter")
        assert isinstance(counter, Counter)
        assert fresh_registry.metric_count == 1

    def test_get_or_create_returns_same_instance(self, fresh_registry):
        c1 = fresh_registry.get_or_create_counter("test")
        c2 = fresh_registry.get_or_create_counter("test")
        assert c1 is c2

    def test_get_or_create_type_mismatch_raises(self, fresh_registry):
        fresh_registry.get_or_create_counter("test")
        with pytest.raises(MetricRegistrationError, match="not a Gauge"):
            fresh_registry.get_or_create_gauge("test")

    def test_unregister(self, fresh_registry):
        fresh_registry.get_or_create_counter("test")
        assert fresh_registry.unregister("test") is True
        assert fresh_registry.metric_count == 0

    def test_unregister_nonexistent(self, fresh_registry):
        assert fresh_registry.unregister("nonexistent") is False

    def test_get_nonexistent_raises(self, fresh_registry):
        with pytest.raises(MetricNotFoundError):
            fresh_registry.get("nonexistent")

    def test_reset_clears_all(self, fresh_registry):
        fresh_registry.get_or_create_counter("c1")
        fresh_registry.freeze()
        fresh_registry.reset()
        assert fresh_registry.metric_count == 0
        assert fresh_registry.is_frozen is False

    def test_clear_returns_count(self, fresh_registry):
        fresh_registry.get_or_create_counter("c1")
        fresh_registry.get_or_create_gauge("g1")
        assert fresh_registry.clear() == 2
        assert fresh_registry.metric_count == 0


# ==========================================================
# 7. Freeze
# ==========================================================

class TestFreeze:
    def test_freeze_prevents_registration(self, fresh_registry):
        fresh_registry.get_or_create_counter("test")
        fresh_registry.freeze()
        with pytest.raises(MetricRegistrationError, match="frozen"):
            fresh_registry.get_or_create_counter("new")

    def test_unfreeze_allows_registration(self, fresh_registry):
        fresh_registry.freeze()
        fresh_registry.unfreeze()
        fresh_registry.get_or_create_counter("test")

    def test_frozen_counter_still_works(self, fresh_registry):
        counter = fresh_registry.get_or_create_counter("test")
        fresh_registry.freeze()
        counter.inc(5)
        assert counter.get() == 5.0


# ==========================================================
# 8. MetricsService
# ==========================================================

class TestMetricsService:
    def test_service_counter(self, fresh_service):
        counter = fresh_service.counter("test")
        counter.inc()
        assert counter.get() == 1.0

    def test_service_timer(self, fresh_service, monkeypatch):
        call_count = [0]
        monkeypatch.setattr(time, "perf_counter", lambda: call_count.__setitem__(0, call_count[0] + 1) or call_count[0] * 0.01)
        with fresh_service.timer("test_duration"):
            pass
        assert list(fresh_service.get("test_duration").collect()["data"].values())[0]["count"] == 1

    def test_service_freeze(self, fresh_service):
        fresh_service.counter("test")
        fresh_service.freeze()
        assert fresh_service.is_frozen is True
        with pytest.raises(MetricRegistrationError):
            fresh_service.counter("new")

    def test_service_health_check(self, fresh_service):
        assert fresh_service.health_check()["healthy"] is True

    def test_service_get_metrics(self, fresh_service):
        fresh_service.counter("c1")
        fresh_service.gauge("g1")
        assert fresh_service.get_metrics()["metric_count"] == 2


# ==========================================================
# 9. Thread-Safety
# ==========================================================

class TestThreadSafety:
    def test_counter_thread_safe(self):
        counter = Counter("c")
        def increment():
            for _ in range(1000):
                counter.inc()
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert counter.get() == 10000

    def test_gauge_thread_safe(self):
        gauge = Gauge("g")
        gauge.set(0)
        def increment():
            for _ in range(100):
                gauge.inc()
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert gauge.get() == 1000


# ==========================================================
# 10. PrometheusExporter
# ==========================================================

class TestPrometheusExporter:
    def test_export_counter(self, fresh_registry):
        fresh_registry.get_or_create_counter("http_requests_total", "Total").inc(10)
        output = PrometheusExporter().export_to_string(fresh_registry)
        assert "# HELP http_requests_total" in output
        assert "# TYPE http_requests_total counter" in output

    def test_export_histogram(self, fresh_registry):
        fresh_registry.get_or_create_histogram("request_duration_seconds").observe(0.5)
        output = PrometheusExporter().export_to_string(fresh_registry)
        assert "# TYPE request_duration_seconds histogram" in output
        assert "_bucket" in output
        assert "_sum" in output
        assert "_count" in output


# ==========================================================
# 11. Integration
# ==========================================================

class TestIntegration:
    def test_full_workflow(self, fresh_service, monkeypatch):
        call_count = [0]
        monkeypatch.setattr(time, "perf_counter", lambda: call_count.__setitem__(0, call_count[0] + 1) or call_count[0] * 0.01)
        requests = fresh_service.counter("http_requests_total", labels=("method", "status"))
        active = fresh_service.gauge("active_connections")
        active.set(5)
        with fresh_service.timer("http_request_duration_seconds"):
            requests.inc(method="GET", status="200")
        active.dec()
        assert requests.get(method="GET", status="200") == 1.0
        assert active.get() == 4.0


# ==========================================================
# 13. Metric.to_dict
# ==========================================================

class TestMetricToDict:
    def test_metric_to_dict(self):
        counter = Counter("td_counter", description="desc", labels=("env",))
        d = counter.to_dict()
        assert d["name"] == "td_counter"
        assert d["description"] == "desc"
        assert d["type"] == "counter"
        assert d["labels"] == ["env"]
        assert "value" in d


# ==========================================================
# 14. Summary trimming
# ==========================================================

class TestSummaryTrimming:
    def test_summary_max_samples_trims(self):
        s = Summary("trim_sum", max_samples=5)
        for i in range(10):
            s.observe(float(i))
        data = list(s.collect()["data"].values())[0]
        assert data["count"] == 10


# ==========================================================
# 15. Timer edge cases
# ==========================================================

class TestTimerEdgeCases:
    def test_timer_exit_without_enter(self):
        h = Histogram("t_exit")
        t = Timer(h)
        t.__exit__(None, None, None)
        assert t.duration is None
        assert h.collect()["data"] == {}

    def test_timer_duration_none_before_enter(self):
        assert Timer(Histogram("t_none")).duration is None


# ==========================================================
# 16. Registry get_or_create all types
# ==========================================================

class TestRegistryGetOrCreateAll:
    def test_get_or_create_gauge(self, fresh_registry):
        g = fresh_registry.get_or_create_gauge("g1")
        assert isinstance(g, Gauge)
        assert fresh_registry.get_or_create_gauge("g1") is g

    def test_get_or_create_histogram(self, fresh_registry):
        h = fresh_registry.get_or_create_histogram("h1")
        assert isinstance(h, Histogram)
        assert fresh_registry.get_or_create_histogram("h1") is h

    def test_get_or_create_summary(self, fresh_registry):
        s = fresh_registry.get_or_create_summary("s1")
        assert isinstance(s, Summary)
        assert fresh_registry.get_or_create_summary("s1") is s


# ==========================================================
# 17. Exporters
# ==========================================================

class TestExporters:
    def test_console_exporter(self, fresh_registry, capsys):
        fresh_registry.get_or_create_counter("c1").inc()
        ConsoleExporter().export(fresh_registry)
        assert "c1" in capsys.readouterr().out

    def test_prometheus_exports_gauge(self, fresh_registry):
        fresh_registry.get_or_create_gauge("g1").set(5)
        assert "# TYPE g1 gauge" in PrometheusExporter().export_to_string(fresh_registry)

    def test_prometheus_exports_summary(self, fresh_registry):
        fresh_registry.get_or_create_summary("s1").observe(1)
        assert "# TYPE s1 summary" in PrometheusExporter().export_to_string(fresh_registry)


# ==========================================================
# 18. MetricsService all types
# ==========================================================

class TestServiceAllTypes:
    def test_service_gauge(self, fresh_service):
        assert isinstance(fresh_service.gauge("sg1"), Gauge)

    def test_service_summary(self, fresh_service):
        assert isinstance(fresh_service.summary("ss1"), Summary)

    def test_service_export(self, fresh_service, capsys):
        fresh_service.export(ConsoleExporter())
        assert capsys.readouterr().out


# ==========================================================
# 19. Registry metadata
# ==========================================================

class TestRegistryMetadata:
    def test_registry_to_dict(self, fresh_registry):
        fresh_registry.get_or_create_counter("td1")
        assert "td1" in fresh_registry.to_dict()

    def test_registry_repr(self, fresh_registry):
        assert "MetricRegistry" in repr(fresh_registry)

    def test_service_repr(self, fresh_service):
        assert "MetricsService" in repr(fresh_service)