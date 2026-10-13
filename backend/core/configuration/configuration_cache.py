"""
HALALIA Configuration Cache
Production Version 1.1 — VERIFIED

المؤسس: جمال الدين زيدان
الحالة: Production Ready ✅

التحسينات المطبقة:
    ✅ استخدام time.monotonic() بدلاً من time.time()
    ✅ إضافة invalidate_prefix() للإبطال الجماعي
    ✅ إضافة touch() لتمديد عمر المدخل
    ✅ إضافة healthy property للمراقبة
    ✅ TODO (Roadmap): MAX_CACHE_SIZE لمنع النمو اللانهائي
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


# ==========================================================
# 1. Internal Data Models
# ==========================================================

@dataclass(slots=True)
class CacheEntry:
    """تمثيل مدخل واحد في الذاكرة المؤقتة"""
    value: Any
    expires_at: float  # Monotonic timestamp بالثواني


# ==========================================================
# 2. Configuration Cache
# ==========================================================

class ConfigurationCache:
    """
    مدير التخزين المؤقت للإعدادات.
    آمن في تعدد المهام (Thread-Safe) ويدعم انتهاء الصلاحية (TTL).
    """

    DEFAULT_TTL_SECONDS: float = 300.0

    def __init__(self, default_ttl: float = DEFAULT_TTL_SECONDS):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    # ======================================================
    # Core Operations
    # ======================================================

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return default

            # ✅ استخدام monotonic clock
            if time.monotonic() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return default

            self._hits += 1
            return entry.value

    # داخل set():
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        # ✅ سياسة واضحة: ttl < 0 → خطأ
        effective_ttl = ttl if ttl is not None else self._default_ttl

        if effective_ttl < 0:
            raise ValueError(
                f"TTL must be non-negative, got {effective_ttl}. "
                f"Use ttl=0 for immediate expiration."
            )

        # ✅ ttl == 0 → لا نخزن (تنتهي فوراً)
        if effective_ttl == 0:
            return

        expires_at = time.monotonic() + effective_ttl

        with self._lock:
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    # ======================================================
    # Prefix-Based Invalidation (جديد)
    # ======================================================

    def invalidate_prefix(self, prefix: str) -> int:
        """
        إبطال جميع المفاتيح التي تبدأ ببادئة معينة.
        مفيد لـ: AI_, DATABASE_, SECURITY_, PROFILE_
        """
        with self._lock:
            keys = [k for k in self._cache if k.startswith(prefix)]
            for key in keys:
                del self._cache[key]
            return len(keys)

    # ======================================================
    # Touch Operation (Memcached-style)
    # ======================================================

    def touch(self, key: str, ttl: Optional[float] = None) -> bool:
        """
        تمديد عمر المدخل دون إعادة كتابته.
        يُرجع True إذا تم التحديث، False إذا لم يكن المفتاح موجوداً أو منتهياً.
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            if time.monotonic() > entry.expires_at:
                del self._cache[key]
                return False

            new_expires = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
            self._cache[key] = CacheEntry(value=entry.value, expires_at=new_expires)
            return True

    # ======================================================
    # Maintenance
    # ======================================================

    def cleanup(self) -> int:
        removed_count = 0
        current_time = time.monotonic()

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry.expires_at
            ]
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1

        return removed_count

    def has(self, key: str) -> bool:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if time.monotonic() > entry.expires_at:
                return False
            return True

    # ======================================================
    # Metrics & Health
    # ======================================================

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def keys(self) -> Tuple[str, ...]:
        with self._lock:
            return tuple(self._cache.keys())

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "size": self.size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "default_ttl_seconds": self._default_ttl
            }

    @property
    def healthy(self) -> bool:
        """هل الذاكرة المؤقتة في حالة صحية جيدة؟ (hit_rate >= 70%)"""
        stats = self.get_stats()
        return stats["hit_rate_percent"] >= 70

    def set_default_ttl(self, ttl: float) -> None:
        with self._lock:
            self._default_ttl = ttl


# ==========================================================
# 3. Explicit Public API
# ==========================================================
__all__ = [
    "ConfigurationCache",
    "CacheEntry",
]