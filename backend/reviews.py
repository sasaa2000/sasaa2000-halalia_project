"""
حلالية - إدارة التقييمات والمراجعات
"""

import logging
from backend.db import db

logger = logging.getLogger(__name__)


def add_review(telegram_id, product_name, rating, comment=None):
    """إضافة تقييم لمنتج"""
    try:
        # 1. التحقق من المستخدم
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return False, "error", "المستخدم غير موجود"

        # 2. التحقق من التقييم (1-5)
        if rating < 1 or rating > 5:
            return False, "error", "التقييم يجب أن يكون بين 1 و 5"

        # 3. البحث عن المنتج
        product = db.execute_one(
            "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_name,)
        )
        if not product:
            return False, "error", "المنتج غير موجود في قاعدة البيانات. يرجى تحليله أولاً."

        # 4. التحقق من عدم وجود تقييم سابق
        existing = db.execute_one(
            """SELECT id, rating, comment FROM reviews 
               WHERE user_id = %s AND product_id = %s""",
            (user['id'], product['id'])
        )

        if existing:
            # تحديث التقييم القديم
            db.execute_query(
                """UPDATE reviews SET rating = %s, comment = %s, created_at = NOW()
                   WHERE id = %s""",
                (rating, comment, existing['id'])
            )
            return True, "updated", rating
        else:
            # إضافة تقييم جديد
            db.execute_query(
                """INSERT INTO reviews (user_id, product_id, rating, comment)
                   VALUES (%s, %s, %s, %s)""",
                (user['id'], product['id'], rating, comment)
            )
            return True, "created", rating

    except Exception as e:
        logger.error(f"❌ خطأ في إضافة التقييم: {e}")
        return False, "error", str(e)

def get_product_reviews(product_name):
    """جلب جميع تقييمات منتج معين"""
    try:
        product = db.execute_one(
            "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_name,)
        )
        if not product:
            return None

        query = """
            SELECT r.rating, r.comment, r.created_at, u.username, u.first_name
            FROM reviews r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.product_id = %s
            ORDER BY r.created_at DESC
        """
        results = db.execute_query(query, (product['id'],), fetch=True)
        reviews = [dict(row) for row in results]

        # حساب الإحصائيات
        if reviews:
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
            rating_counts = {i: sum(1 for r in reviews if r['rating'] == i) for i in range(1, 6)}
        else:
            avg_rating = 0
            rating_counts = {i: 0 for i in range(1, 6)}

        return {
            "product_name": product_name,
            "total_reviews": len(reviews),
            "average_rating": round(avg_rating, 1),
            "rating_counts": rating_counts,
            "reviews": reviews
        }
    except Exception as e:
        logger.error(f"❌ خطأ في جلب التقييمات: {e}")
        return None


def get_user_reviews(telegram_id):
    """جلب جميع تقييمات المستخدم"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return []

        query = """
            SELECT p.product_name, r.rating, r.comment, r.created_at
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        """
        results = db.execute_query(query, (user['id'],), fetch=True)
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"❌ خطأ في جلب تقييمات المستخدم: {e}")
        return []


def delete_review(telegram_id, product_name):
    """حذف تقييم المستخدم لمنتج معين"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return False

        product = db.execute_one(
            "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_name,)
        )
        if not product:
            return False

        db.execute_query(
            "DELETE FROM reviews WHERE user_id = %s AND product_id = %s",
            (user['id'], product['id'])
        )
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حذف التقييم: {e}")
        return False