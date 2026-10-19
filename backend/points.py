"""
حلالية - نظام النقاط والشارات
"""
import logging
from backend.db import db

logger = logging.getLogger(__name__)

POINTS_RULES = {
    "search": 10,
    "save": 15,
    "review": 20,
    "alert": 10,
    "wishlist_create": 25,
    "wishlist_add": 10,
    "compare": 15,
    "gifts": 5,
    "category": 5,
}

BADGES = [
    {"min_points": 0, "name": "مستكشفة 🌱", "level": 1},
    {"min_points": 100, "name": "متسوقة نشطة 🛍️", "level": 2},
    {"min_points": 250, "name": "خبيرة تسوق 💎", "level": 3},
    {"min_points": 500, "name": "ملكة التسوق 👑", "level": 4},
    {"min_points": 1000, "name": "أسطورة حلالية 🏆", "level": 5},
]

def get_or_create_user_points(telegram_id):
    try:
        user = db.execute_one("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        if not user: return None

        points_record = db.execute_one("SELECT * FROM user_points WHERE user_id = %s", (user['id'],))
        if not points_record:
            db.execute_query(
                "INSERT INTO user_points (user_id, total_points, current_badge, level) VALUES (%s, 0, 'مستكشفة 🌱', 1)",
                (user['id'],)
            )
            points_record = db.execute_one("SELECT * FROM user_points WHERE user_id = %s", (user['id'],))
        return dict(points_record)
    except Exception as e:
        logger.error(f"خطأ في جلب نقاط المستخدم: {e}")
        return None

def add_points(telegram_id, action, description=None):
    try:
        user = db.execute_one("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        if not user: return False

        points = POINTS_RULES.get(action, 0)
        if points == 0: return False

        current = get_or_create_user_points(telegram_id)
        if not current: return False

        new_total = current['total_points'] + points
        new_badge = current['current_badge']
        new_level = current['level']

        for badge in reversed(BADGES):
            if new_total >= badge['min_points']:
                if badge['name'] != current['current_badge']:
                    new_badge = badge['name']
                    new_level = badge['level']
                break

        db.execute_query(
            "UPDATE user_points SET total_points = %s, current_badge = %s, level = %s, updated_at = NOW() WHERE user_id = %s",
            (new_total, new_badge, new_level, user['id'])
        )

        db.execute_query(
            "INSERT INTO points_history (user_id, action, points, description) VALUES (%s, %s, %s, %s)",
            (user['id'], action, points, description)
        )

        return {
            "points_added": points,
            "new_total": new_total,
            "badge": new_badge,
            "level": new_level,
            "leveled_up": new_badge != current['current_badge']
        }
    except Exception as e:
        logger.error(f"خطأ في إضافة النقاط: {e}")
        return False

def get_user_profile(telegram_id):
    try:
        user = db.execute_one(
            """SELECT u.telegram_id, u.username, u.first_name, u.created_at as member_since,
                      up.total_points, up.current_badge, up.level,
                      up.searches_count, up.saves_count, up.reviews_count
               FROM users u LEFT JOIN user_points up ON u.id = up.user_id WHERE u.telegram_id = %s""",
            (telegram_id,)
        )
        if not user: return None
        result = dict(user)

        next_badge = None
        for badge in BADGES:
            if badge['min_points'] > result.get('total_points', 0):
                next_badge = badge
                break

        if next_badge:
            result['points_to_next'] = next_badge['min_points'] - result.get('total_points', 0)
            result['next_badge'] = next_badge['name']
        else:
            result['points_to_next'] = 0
            result['next_badge'] = "أعلى شارة!"

        history = db.execute_query(
            """SELECT action, points, description, created_at FROM points_history
               WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s) ORDER BY created_at DESC LIMIT 5""",
            (telegram_id,), fetch=True
        )
        result['recent_activity'] = [dict(h) for h in history] if history else []
        return result
    except Exception as e:
        logger.error(f"خطأ في جلب الملف الشخصي: {e}")
        return None