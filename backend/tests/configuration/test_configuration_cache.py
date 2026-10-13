"""
اختبارات الوحدة لـ ConfigurationCache — v1.0

يغطي:
    ✅ set() / get() أساسيان
    ✅ get() مع Default Value
    ✅ TTL — انتهاء الصلاحية
    ✅ Lazy Expiration — الحذف عند get() بعد انتهاء TTL
    ✅ delete() — إبطال قيمة
    ✅ clear() — مسح الكل
    ✅ cleanup() — تنظيف منتهي الصلاحية
    ✅ has() — مفتاح صالح / منتهي / غير موجود
    ✅ size / keys properties
    ✅ get_stats() — hits, misses, hit_rate
    ✅ healthy property
    ✅ set_default_ttl()
    ✅ Thread Safety
    ✅ Edge Cases (None, empty key, overwrite)

عدد الاختبارات: 24
"""

from __future__ import annotations

import threading
import time

import pytest

from core.configuration.configuration_cache import (
    ConfigurationCache,
)


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def cache():
    """ConfigurationCache جديد لكل اختبار"""
    return ConfigurationCache(default_ttl=300.0)


@pytest.fixture
def short_ttl_cache():
    """Cache مع TTL قصير جداً (0.1 ثانية)"""
    return ConfigurationCache(default_ttl=0.1)


# ==========================================================
# 1. Basic set() / get() Tests (4)
# ==========================================================

class TestBasicOperations:
    def test_set_and_get(self, cache):
        """set() ثم get() يُرجع القيمة"""
        cache.set("APP_NAME", "HALALIA")
        assert cache.get("APP_NAME") == "HALALIA"

    def test_get_missing_key_returns_none(self, cache):
        """get() لمفتاح غير موجود يُرجع None"""
        assert cache.get("NONEXISTENT") is None

    def test_get_missing_key_custom_default(self, cache):
        """get() لمفتاح غير موجود مع default مخصص"""
        assert cache.get("NONEXISTENT", "fallback") == "fallback"

    def test_overwrite_value(self, cache):
        """set() يستبدل القيمة السابقة"""
        cache.set("KEY", "old")
        cache.set("KEY", "new")
        assert cache.get("KEY") == "new"


# ==========================================================
# 2. TTL Tests (4)
# ==========================================================

class TestTTL:
    def test_value_valid_before_ttl(self, cache):
        """القيمة صالحة قبل انتهاء TTL"""
        cache.set("KEY", "value", ttl=10.0)
        assert cache.get("KEY") == "value"

    def test_value_expired_after_ttl(self, monkeypatch):
        """القيمة تنتهي بعد TTL"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=5.0)
        cache.set("KEY", "value")

        # قبل انتهاء TTL
        assert cache.get("KEY") == "value"

        # بعد انتهاء TTL (نحرك الوقت 6 ثوانٍ)
        current_time[0] = 1006.0
        assert cache.get("KEY") is None

    def test_custom_ttl_per_key(self, monkeypatch):
        """TTL مخصص لكل مفتاح"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=300.0)
        cache.set("SHORT", "value", ttl=2.0)
        cache.set("LONG", "value", ttl=100.0)

        # بعد 3 ثوانٍ: SHORT انتهى، LONG ما زال صالحاً
        current_time[0] = 1003.0
        assert cache.get("SHORT") is None
        assert cache.get("LONG") == "value"

    def test_default_ttl_used_when_not_specified(self, monkeypatch):
        """TTL الافتراضي يُستخدم عندما لا يُحدد"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=5.0)
        cache.set("KEY", "value")  # بدون ttl

        current_time[0] = 1006.0
        assert cache.get("KEY") is None


# ==========================================================
# 3. Lazy Expiration Tests (2)
# ==========================================================

class TestLazyExpiration:
    def test_expired_value_removed_on_get(self, monkeypatch):
        """القيمة المنتهية تُحذف عند get()"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=1.0)
        cache.set("KEY", "value")

        assert cache.size == 1

        # بعد انتهاء TTL
        current_time[0] = 1002.0
        cache.get("KEY")  # يجب أن يحذف القيمة

        assert cache.size == 0

    def test_has_returns_false_for_expired(self, monkeypatch):
        """has() يُرجع False للقيم المنتهية"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=1.0)
        cache.set("KEY", "value")

        assert cache.has("KEY") is True

        current_time[0] = 1002.0
        assert cache.has("KEY") is False


# ==========================================================
# 4. delete() Tests (2)
# ==========================================================

class TestDelete:
    def test_delete_existing_key(self, cache):
        """delete() يزيل المفتاح"""
        cache.set("KEY", "value")
        result = cache.delete("KEY")
        assert result is True
        assert cache.get("KEY") is None

    def test_delete_nonexistent_key(self, cache):
        """delete() لمفتاح غير موجود يُرجع False"""
        result = cache.delete("NONEXISTENT")
        assert result is False


# ==========================================================
# 5. clear() Tests (1)
# ==========================================================

class TestClear:
    def test_clear_removes_all(self, cache):
        """clear() يمسح جميع القيم"""
        cache.set("A", "1")
        cache.set("B", "2")
        cache.set("C", "3")

        assert cache.size == 3

        cache.clear()

        assert cache.size == 0
        assert cache.get("A") is None
        assert cache.get("B") is None
        assert cache.get("C") is None


# ==========================================================
# 6. cleanup() Tests (2)
# ==========================================================

class TestCleanup:
    def test_cleanup_removes_expired(self, monkeypatch):
        """cleanup() يزيل القيم المنتهية فقط"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=5.0)
        cache.set("SHORT", "value", ttl=1.0)
        cache.set("LONG", "value", ttl=100.0)

        current_time[0] = 1002.0
        removed = cache.cleanup()

        assert removed == 1
        assert cache.get("SHORT") is None
        assert cache.get("LONG") == "value"

    def test_cleanup_returns_zero_when_nothing_expired(self, cache):
        """cleanup() يُرجع 0 عندما لا يوجد منتهي"""
        cache.set("KEY", "value", ttl=1000.0)
        removed = cache.cleanup()
        assert removed == 0


# ==========================================================
# 7. has() Tests (3)
# ==========================================================

class TestHas:
    def test_has_existing_key(self, cache):
        assert cache.has("NONEXISTENT") is False
        cache.set("KEY", "value")
        assert cache.has("KEY") is True

    def test_has_after_delete(self, cache):
        cache.set("KEY", "value")
        cache.delete("KEY")
        assert cache.has("KEY") is False

    def test_has_after_clear(self, cache):
        cache.set("KEY", "value")
        cache.clear()
        assert cache.has("KEY") is False


# ==========================================================
# 8. size / keys Properties (2)
# ==========================================================

class TestProperties:
    def test_size(self, cache):
        assert cache.size == 0
        cache.set("A", "1")
        cache.set("B", "2")
        assert cache.size == 2

    def test_keys(self, cache):
        cache.set("A", "1")
        cache.set("B", "2")
        keys = cache.keys
        assert "A" in keys
        assert "B" in keys
        assert len(keys) == 2


# ==========================================================
# 9. get_stats() Tests (3)
# ==========================================================

class TestStats:
    def test_stats_initial(self, cache):
        """الإحصائيات الأولية"""
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate_percent"] == 0.0

    def test_stats_hits_and_misses(self, cache):
        """الإحصائيات بعد عمليات"""
        cache.set("KEY", "value")

        cache.get("KEY")  # hit
        cache.get("KEY")  # hit
        cache.get("MISSING")  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1

    def test_stats_hit_rate(self, cache):
        """حساب hit_rate"""
        cache.set("KEY", "value")

        # 3 hits, 1 miss → 75%
        cache.get("KEY")
        cache.get("KEY")
        cache.get("KEY")
        cache.get("MISSING")

        stats = cache.get_stats()
        assert stats["hit_rate_percent"] == 75.0


# ==========================================================
# 10. healthy Property (2)
# ==========================================================

class TestHealthy:
    def test_healthy_when_high_hit_rate(self, cache):
        """healthy = True عندما يكون hit_rate >= 70%"""
        cache.set("KEY", "value")

        # 10 hits, 0 misses → 100%
        for _ in range(10):
            cache.get("KEY")

        assert cache.healthy is True

    def test_unhealthy_when_low_hit_rate(self, cache):
        """healthy = False عندما يكون hit_rate < 70%"""
        cache.set("KEY", "value")

        # 1 hit, 10 misses → ~9%
        cache.get("KEY")
        for _ in range(10):
            cache.get(f"MISSING_{_}")

        assert cache.healthy is False


# ==========================================================
# 11. set_default_ttl() (1)
# ==========================================================

class TestSetDefaultTTL:
    def test_set_default_ttl(self, monkeypatch):
        """set_default_ttl() يغير TTL الافتراضي"""
        current_time = [1000.0]

        def mock_monotonic():
            return current_time[0]

        monkeypatch.setattr(
            "core.configuration.configuration_cache.time.monotonic",
            mock_monotonic
        )

        cache = ConfigurationCache(default_ttl=5.0)
        cache.set_default_ttl(1.0)

        cache.set("KEY", "value")  # سيستخدم TTL الجديد (1.0)

        current_time[0] = 1002.0
        assert cache.get("KEY") is None


# ==========================================================
# 12. Thread Safety Tests (2)
# ==========================================================

class TestThreadSafety:
    def test_concurrent_set_and_get(self, cache):
        """set() و get() معاً آمنان"""
        errors = []

        def writer():
            try:
                for i in range(100):
                    cache.set(f"KEY_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(100):
                    cache.get(f"KEY_{i}")
            except Exception as e:
                errors.append(e)

        threads = (
                [threading.Thread(target=writer) for _ in range(5)] +
                [threading.Thread(target=reader) for _ in range(5)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_set_no_data_loss(self, cache):
        """لا فقدان بيانات مع set() المتزامن"""
        num_threads = 10
        keys_per_thread = 100

        def writer(thread_id):
            for i in range(keys_per_thread):
                cache.set(f"T{thread_id}_K{i}", f"V{thread_id}_{i}")

        threads = [
            threading.Thread(target=writer, args=(t,))
            for t in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # ✅ التحقق من عدم فقدان البيانات
        expected_count = num_threads * keys_per_thread
        assert cache.size == expected_count

        # التحقق من صحة القيم
        for t in range(num_threads):
            for i in range(keys_per_thread):
                assert cache.get(f"T{t}_K{i}") == f"V{t}_{i}"


# ==========================================================
# 13. Edge Cases (3)
# ==========================================================

class TestEdgeCases:
    def test_set_none_value(self, cache):
        """set() مع None كقيمة"""
        cache.set("KEY", None)
        # None قيمة صالحة (ليست "لا يوجد")
        assert cache.has("KEY") is True

    def test_set_empty_string_value(self, cache):
        """set() مع سلسلة فارغة"""
        cache.set("KEY", "")
        assert cache.get("KEY") == ""

    def test_set_complex_value(self, cache):
        """set() مع قيمة معقدة (dict)"""
        complex_value = {"nested": {"key": [1, 2, 3]}}
        cache.set("KEY", complex_value)
        assert cache.get("KEY") == complex_value

    def test_rapid_set_get_cycles(self, cache):
        """دورات set/get سريعة"""
        for i in range(1000):
            cache.set("KEY", f"value_{i}")
            assert cache.get("KEY") == f"value_{i}"