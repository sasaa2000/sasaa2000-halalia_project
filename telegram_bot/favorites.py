"""
حلالية - إدارة المفضلة باستخدام PostgreSQL
"""

import logging
from backend.db import db

logger = logging.getLogger(__name__)


def get_or_create_user(telegram_id, username=None, first_name=None):
    """الحصول على المستخدم أو إنشاؤه"""
    try:
        # البحث عن المستخدم
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )

        if user:
            # تحديث آخر نشاط
            db.execute_query(
                "UPDATE users SET last_active = NOW() WHERE id = %s",
                (user['id'],)
            )
            return user['id']
        else:
            # إنشاء مستخدم جديد
            result = db.execute_one(
                """INSERT INTO users (telegram_id, username, first_name) 
                   VALUES (%s, %s, %s) RETURNING id""",
                (telegram_id, username, first_name)
            )
            logger.info(f"✅ تم إنشاء مستخدم جديد: {telegram_id}")
            return result['id']
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة المستخدم: {e}")
        return None


def add_favorite(user_telegram_id, product_data, username=None, first_name=None):
    """إضافة منتج إلى المفضلة"""
    try:
        user_id = get_or_create_user(user_telegram_id, username, first_name)
        if not user_id:
            return False

        # البحث عن المنتج بالاسم
        product = db.execute_one(
            "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_data.get("product_name"),)
        )

        if not product:
            # إذا لم يكن المنتج موجوداً، نحفظه أولاً
            from backend.database import save_product
            save_product(product_data)
            product = db.execute_one(
                "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
                (product_data.get("product_name"),)
            )

        if not product:
            return False

        # إضافة إلى المفضلة
        db.execute_query(
            """INSERT INTO favorites (user_id, product_id) 
               VALUES (%s, %s) 
               ON CONFLICT (user_id, product_id) DO NOTHING""",
            (user_id, product['id'])
        )

        logger.info(f"✅ تم إضافة {product_data.get('product_name')} إلى مفضلة المستخدم {user_telegram_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة المفضلة: {e}")
        return False


def remove_favorite(user_telegram_id, product_name):
    """حذف منتج من المفضلة"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (user_telegram_id,)
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
            "DELETE FROM favorites WHERE user_id = %s AND product_id = %s",
            (user['id'], product['id'])
        )

        logger.info(f"✅ تم حذف {product_name} من مفضلة المستخدم {user_telegram_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حذف المفضلة: {e}")
        return False


def get_user_favorites(user_telegram_id):
    """الحصول على منتجات مفضلة المستخدم"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (user_telegram_id,)
        )

        if not user:
            return []

        query = """
            SELECT p.* FROM products p
            INNER JOIN favorites f ON p.id = f.product_id
            WHERE f.user_id = %s
            ORDER BY f.added_at DESC
        """

        results = db.execute_query(query, (user['id'],), fetch=True)

        favorites = []
        for row in results:
            product = dict(row)
            if product.get('amazon_market'):
                product['amazon_market'] = dict(product['amazon_market'])
            favorites.append(product)

        return favorites
    except Exception as e:
        logger.error(f"❌ خطأ في جلب المفضلة: {e}")
        return []


def get_user_stats(user_telegram_id):
    """الحصول على إحصائيات المستخدم"""
    try:
        user = db.execute_one(
            """SELECT u.*, 
                      COUNT(f.id) as favorites_count,
                      COUNT(DISTINCT p.id) as searched_products
               FROM users u
               LEFT JOIN favorites f ON u.id = f.user_id
               LEFT JOIN products p ON u.id = p.id
               WHERE u.telegram_id = %s
               GROUP BY u.id""",
            (user_telegram_id,)
        )
        return dict(user) if user else None
    except Exception as e:
        logger.error(f"❌ خطأ في جلب إحصائيات المستخدم: {e}")
        return None