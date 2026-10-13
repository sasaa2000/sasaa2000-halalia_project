"""
HALALIA Metrics System
Production Version 1.2.0 — VERIFIED (Testable Singleton)

التحسينات في v1.2.0:
    ✅ إضافة reset() إلى MetricRegistry و MetricsService
    ✅ إضافة reset_instance() classmethod للاختبارات
    ✅ Singleton قابل للاختبار بدون __new__ hacks
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ==========================================================
# 1. Constants
# ==========================================================

METRICS_VERSION = "1.2.0"


# ==========================================================
# 2. Enums
# ==========================================================

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


# ==========================================================
# 3. Exceptions
# ==========================================================

class MetricRegistrationError(ValueError):
    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"Cannot register metric '{name}': {reason}")


class MetricNotFoundError(KeyError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Metric not found: '{name}'")


# ==========================================================
# 4. Base Metric Class
# ==========================================================

class Metric(ABC):
    def __init__(
            self,
            name: str,
            description: str = "",
            labels: Tuple[str, ...] = (),
    ):
        if not name or not isinstance(name, str):
            raise MetricRegistrationError(name, "Name must be a non-empty string")

        self._name = name
        self._description = description
        self._labels = labels
        self._created_at = time.time()
        self._lock = threading.RLock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def labels(self) -> Tuple[str, ...]:
        return self._labels

    @property
    @abstractmethod
    def metric_type(self) -> MetricType:
        pass

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "description": self._description,
            "type": self.metric_type.value,
            "labels": list(self._labels),
            "created_at": self._created_at,
            "value": self.collect(),
        }

    def _label_key(self, **label_values) -> Tuple[str, ...]:
        return tuple(str(label_values.get(label, "")) for label in self._labels)


# ==========================================================
# 5. Counter
# ==========================================================

class Counter(Metric):
    def __init__(self, name: str, description: str = "", labels: Tuple[str, ...] = ()):
        super().__init__(name, description, labels)
        self._values: Dict[Tuple[str, ...], float] = defaultdict(float)

    @property
    def metric_type(self) -> MetricType:
        return MetricType.COUNTER

    def inc(self, amount: float = 1.0, **label_values) -> None:
        if amount < 0:
            raise ValueError("Counter can only be incremented by non-negative amounts")
        key = self._label_key(**label_values)
        with self._lock:
            self._values[key] += amount

    def get(self, **label_values) -> float:
        key = self._label_key(**label_values)
        with self._lock:
            return self._values.get(key, 0.0)

    def collect(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "type": "counter",
                "values": {str(k): v for k, v in self._values.items()},
                "total": sum(self._values.values()),
            }


# ==========================================================
# 6. Gauge
# ==========================================================

class Gauge(Metric):
    def __init__(self, name: str, description: str = "", labels: Tuple[str, ...] = ()):
        super().__init__(name, description, labels)
        self._values: Dict[Tuple[str, ...], float] = defaultdict(float)

    @property
    def metric_type(self) -> MetricType:
        return MetricType.GAUGE

    def set(self, value: float, **label_values) -> None:
        key = self._label_key(**label_values)
        with self._lock:
            self._values[key] = value

    def inc(self, amount: float = 1.0, **label_values) -> None:
        key = self._label_key(**label_values)
        with self._lock:
            self._values[key] += amount

    def dec(self, amount: float = 1.0, **label_values) -> None:
        key = self._label_key(**label_values)
        with self._lock:
            self._values[key] -= amount

    def get(self, **label_values) -> float:
        key = self._label_key(**label_values)
        with self._lock:
            return self._values.get(key, 0.0)

    def collect(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "type": "gauge",
                "values": {str(k): v for k, v in self._values.items()},
            }


# ==========================================================
# 7. Histogram
# ==========================================================

class Histogram(Metric):
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(
            self,
            name: str,
            description: str = "",
            labels: Tuple[str, ...] = (),
            buckets: Tuple[float, ...] = DEFAULT_BUCKETS,
    ):
        super().__init__(name, description, labels)
        self._buckets = tuple(sorted(buckets))
        self._data: Dict[Tuple[str, ...], Dict[str, Any]] = {}

    @property
    def metric_type(self) -> MetricType:
        return MetricType.HISTOGRAM

    def observe(self, value: float, **label_values) -> None:
        key = self._label_key(**label_values)
        with self._lock:
            if key not in self._data:
                self._data[key] = {
                    "buckets": {b: 0 for b in self._buckets},
                    "sum": 0.0,
                    "count": 0,
                }
            data = self._data[key]
            data["sum"] += value
            data["count"] += 1
            for bucket in self._buckets:
                if value <= bucket:
                    data["buckets"][bucket] += 1

    def collect(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "type": "histogram",
                "buckets": list(self._buckets),
                "data": {str(k): v for k, v in self._data.items()},
            }


# ==========================================================
# 8. Summary
# ==========================================================

class Summary(Metric):
    DEFAULT_QUANTILES = (0.5, 0.9, 0.95, 0.99)

    def __init__(
            self,
            name: str,
            description: str = "",
            labels: Tuple[str, ...] = (),
            quantiles: Tuple[float, ...] = DEFAULT_QUANTILES,
            max_samples: int = 10000,
    ):
        super().__init__(name, description, labels)
        self._quantiles = tuple(sorted(quantiles))
        self._max_samples = max_samples
        self._data: Dict[Tuple[str, ...], Dict[str, Any]] = {}

    @property
    def metric_type(self) -> MetricType:
        return MetricType.SUMMARY

    def observe(self, value: float, **label_values) -> None:
        key = self._label_key(**label_values)
        with self._lock:
            if key not in self._data:
                self._data[key] = {"samples": [], "sum": 0.0, "count": 0}
            data = self._data[key]
            data["samples"].append(value)
            data["sum"] += value
            data["count"] += 1
            if len(data["samples"]) > self._max_samples:
                data["samples"] = data["samples"][-self._max_samples:]

    def _calculate_quantile(self, samples: List[float], q: float) -> float:
        if not samples:
            return 0.0
        sorted_samples = sorted(samples)
        idx = int(q * (len(sorted_samples) - 1))
        return sorted_samples[idx]

    def collect(self) -> Dict[str, Any]:
        with self._lock:
            result = {"type": "summary", "data": {}}
            for key, data in self._data.items():
                quantile_values = {
                    f"q{q}": self._calculate_quantile(data["samples"], q)
                    for q in self._quantiles
                }
                result["data"][str(key)] = {
                    "quantiles": quantile_values,
                    "sum": data["sum"],
                    "count": data["count"],
                }
            return result


# ==========================================================
# 9. Timer
# ==========================================================

class Timer:
    def __init__(self, histogram: Histogram, **label_values):
        self._histogram = histogram
        self._label_values = label_values
        self._start_time: Optional[float] = None
        self._duration: Optional[float] = None

    def __enter__(self) -> "Timer":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._start_time is not None:
            self._duration = time.perf_counter() - self._start_time
            self._histogram.observe(self._duration, **self._label_values)

    @property
    def duration(self) -> Optional[float]:
        return self._duration


# ==========================================================
# 10. Metric Registry (✅ Testable Singleton)
# ==========================================================

class MetricRegistry:
    """السجل المركزي لجميع العدادات — Singleton قابل للاختبار"""

    _instance: Optional["MetricRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._metrics: Dict[str, Metric] = {}
        self._registry_lock = threading.RLock()
        self._registration_count = 0
        self._collection_count = 0
        self._frozen = False

    # ✅ للاختبارات: إعادة تعيين المثيل بالكامل
    @classmethod
    def reset_instance(cls) -> None:
        """إعادة تعيين Singleton (للاختبارات فقط)"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
            cls._instance = None

    # ✅ API عام للمسح (بدلاً من لمس _metrics)
    def reset(self) -> None:
        """مسح جميع العدادات وإعادة تعيين الحالة"""
        with self._registry_lock:
            self._metrics.clear()
            self._registration_count = 0
            self._collection_count = 0
            self._frozen = False

    def clear(self) -> int:
        """مسح جميع العدادات (يُرجع العدد المحذوف)"""
        with self._registry_lock:
            count = len(self._metrics)
            self._metrics.clear()
            return count

    def register(self, metric: Metric) -> Metric:
        if self._frozen:
            raise MetricRegistrationError(metric.name, "Registry is frozen")
        with self._registry_lock:
            if metric.name in self._metrics:
                raise MetricRegistrationError(metric.name, "Already exists")
            self._metrics[metric.name] = metric
            self._registration_count += 1
            return metric

    def get(self, name: str) -> Metric:
        with self._registry_lock:
            if name not in self._metrics:
                raise MetricNotFoundError(name)
            return self._metrics[name]

    def get_or_create_counter(self, name: str, description: str = "", labels: Tuple[str, ...] = ()) -> Counter:
        with self._registry_lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Counter):
                    raise MetricRegistrationError(name, "Exists but is not a Counter")
                return metric
            if self._frozen:
                raise MetricRegistrationError(name, "Registry is frozen")
            counter = Counter(name, description, labels)
            self._metrics[name] = counter
            self._registration_count += 1
            return counter

    def get_or_create_gauge(self, name: str, description: str = "", labels: Tuple[str, ...] = ()) -> Gauge:
        with self._registry_lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Gauge):
                    raise MetricRegistrationError(name, "Exists but is not a Gauge")
                return metric
            if self._frozen:
                raise MetricRegistrationError(name, "Registry is frozen")
            gauge = Gauge(name, description, labels)
            self._metrics[name] = gauge
            self._registration_count += 1
            return gauge

    def get_or_create_histogram(self, name: str, description: str = "", labels: Tuple[str, ...] = (),
                                buckets: Tuple[float, ...] = Histogram.DEFAULT_BUCKETS) -> Histogram:
        with self._registry_lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Histogram):
                    raise MetricRegistrationError(name, "Exists but is not a Histogram")
                return metric
            if self._frozen:
                raise MetricRegistrationError(name, "Registry is frozen")
            histogram = Histogram(name, description, labels, buckets)
            self._metrics[name] = histogram
            self._registration_count += 1
            return histogram

    def get_or_create_summary(self, name: str, description: str = "", labels: Tuple[str, ...] = (),
                              quantiles: Tuple[float, ...] = Summary.DEFAULT_QUANTILES) -> Summary:
        with self._registry_lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Summary):
                    raise MetricRegistrationError(name, "Exists but is not a Summary")
                return metric
            if self._frozen:
                raise MetricRegistrationError(name, "Registry is frozen")
            summary = Summary(name, description, labels, quantiles)
            self._metrics[name] = summary
            self._registration_count += 1
            return summary

    def unregister(self, name: str) -> bool:
        if self._frozen:
            raise MetricRegistrationError(name, "Registry is frozen")
        with self._registry_lock:
            if name in self._metrics:
                del self._metrics[name]
                return True
            return False

    def collect_all(self) -> Dict[str, Any]:
        with self._registry_lock:
            self._collection_count += 1
            return {name: metric.collect() for name, metric in self._metrics.items()}

    def to_dict(self) -> Dict[str, Any]:
        with self._registry_lock:
            return {name: metric.to_dict() for name, metric in self._metrics.items()}

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    @property
    def metric_count(self) -> int:
        with self._registry_lock:
            return len(self._metrics)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "version": METRICS_VERSION,
            "metric_count": self.metric_count,
            "registration_count": self._registration_count,
            "collection_count": self._collection_count,
            "frozen": self._frozen,
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "healthy": self._initialized,
            "metric_count": self.metric_count,
            "frozen": self._frozen,
        }

    def __repr__(self) -> str:
        return f"<MetricRegistry metrics={self.metric_count} frozen={self._frozen}>"


# ==========================================================
# 11. Exporters
# ==========================================================

class MetricExporter(ABC):
    @abstractmethod
    def export(self, registry: MetricRegistry) -> None:
        pass


class ConsoleExporter(MetricExporter):
    def export(self, registry: MetricRegistry) -> None:
        import json
        print(json.dumps(registry.to_dict(), indent=2, default=str))


class PrometheusExporter(MetricExporter):
    def export(self, registry: MetricRegistry) -> None:
        print(self.export_to_string(registry))

    def export_to_string(self, registry: MetricRegistry) -> str:
        lines = []
        for name, metric in registry._metrics.items():
            lines.append(f"# HELP {name} {metric.description or name}")
            lines.append(f"# TYPE {name} {metric.metric_type.value}")
            collected = metric.collect()
            if metric.metric_type == MetricType.COUNTER:
                for labels_str, value in collected.get("values", {}).items():
                    lines.append(f"{name}{{labels={labels_str}}} {value}")
            elif metric.metric_type == MetricType.GAUGE:
                for labels_str, value in collected.get("values", {}).items():
                    lines.append(f"{name}{{labels={labels_str}}} {value}")
            elif metric.metric_type == MetricType.HISTOGRAM:
                for labels_str, data in collected.get("data", {}).items():
                    for bucket, count in data.get("buckets", {}).items():
                        lines.append(f'{name}_bucket{{le="{bucket}",labels={labels_str}}} {count}')
                    lines.append(f'{name}_sum{{labels={labels_str}}} {data.get("sum", 0)}')
                    lines.append(f'{name}_count{{labels={labels_str}}} {data.get("count", 0)}')
            lines.append("")
        return "\n".join(lines)


# ==========================================================
# 12. Metrics Service (✅ Testable Singleton)
# ==========================================================

class MetricsService:
    _instance: Optional["MetricsService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricsService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._registry = MetricRegistry()

    @classmethod
    def reset_instance(cls) -> None:
        """إعادة تعيين Singleton (للاختبارات فقط)"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
            cls._instance = None

    def counter(self, name: str, description: str = "", labels: Tuple[str, ...] = ()) -> Counter:
        return self._registry.get_or_create_counter(name, description, labels)

    def gauge(self, name: str, description: str = "", labels: Tuple[str, ...] = ()) -> Gauge:
        return self._registry.get_or_create_gauge(name, description, labels)

    def histogram(self, name: str, description: str = "", labels: Tuple[str, ...] = (),
                  buckets: Tuple[float, ...] = Histogram.DEFAULT_BUCKETS) -> Histogram:
        return self._registry.get_or_create_histogram(name, description, labels, buckets)

    def summary(self, name: str, description: str = "", labels: Tuple[str, ...] = (),
                quantiles: Tuple[float, ...] = Summary.DEFAULT_QUANTILES) -> Summary:
        return self._registry.get_or_create_summary(name, description, labels, quantiles)

    def timer(self, name: str, **label_values) -> Timer:
        histogram = self._registry.get_or_create_histogram(name, description=f"Timer for {name}")
        return Timer(histogram, **label_values)

    @property
    def registry(self) -> MetricRegistry:
        return self._registry

    def get(self, name: str) -> Metric:
        return self._registry.get(name)

    def collect_all(self) -> Dict[str, Any]:
        return self._registry.collect_all()

    def export(self, exporter: MetricExporter) -> None:
        exporter.export(self._registry)

    def freeze(self) -> None:
        self._registry.freeze()

    def unfreeze(self) -> None:
        self._registry.unfreeze()

    @property
    def is_frozen(self) -> bool:
        return self._registry.is_frozen

    def health_check(self) -> Dict[str, Any]:
        return self._registry.health_check()

    def get_metrics(self) -> Dict[str, Any]:
        return self._registry.get_metrics()

    @property
    def version(self) -> str:
        return METRICS_VERSION

    def __repr__(self) -> str:
        return f"<MetricsService metrics={self._registry.metric_count} frozen={self.is_frozen}>"


# ==========================================================
# 13. Global Instances
# ==========================================================
metrics_registry = MetricRegistry()
metrics_service = MetricsService()

# ==========================================================
# 14. Explicit Public API
# ==========================================================
__all__ = [
    "METRICS_VERSION",
    "MetricType",
    "MetricRegistrationError",
    "MetricNotFoundError",
    "Metric",
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    "Timer",
    "MetricRegistry",
    "MetricExporter",
    "ConsoleExporter",
    "PrometheusExporter",
    "MetricsService",
    "metrics_registry",
    "metrics_service",
]