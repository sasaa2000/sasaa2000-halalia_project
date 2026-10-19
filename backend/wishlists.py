"""
حلالية - إدارة قوائم الرغبات (Wishlists)
"""

import logging
import uuid
from backend.db import db

logger = logging.getLogger(__name__)


def create_wishlist(telegram_id, name, description=None):
    """إنشاء قائمة رغبات جديدة"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return False, "المستخدم غير موجود"

        # توليد رمز مشاركة فريد
        share_token = str(uuid.uuid4())[:12]

        result = db.execute_one(
            """INSERT INTO wishlists (user_id, name, description, share_token)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (user['id'], name, description, share_token)
        )

        return True, result['id']
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء قائمة الرغبات: {e}")
        return False, str(e)


def get_user_wishlists(telegram_id):
    """جلب جميع قوائم المستخدم"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return []

        query = """
            SELECT w.id, w.name, w.description, w.share_token, w.is_public, w.created_at,
                   COUNT(wi.id) as items_count
            FROM wishlists w
            LEFT JOIN wishlist_items wi ON w.id = wi.wishlist_id
            WHERE w.user_id = %s
            GROUP BY w.id
            ORDER BY w.created_at DESC
        """
        results = db.execute_query(query, (user['id'],), fetch=True)
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"❌ خطأ في جلب قوائم الرغبات: {e}")
        return []


def add_to_wishlist(telegram_id, wishlist_id, product_name, note=None):
    """إضافة منتج إلى قائمة رغبات"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return False, "المستخدم غير موجود"

        # التحقق من ملكية القائمة
        wishlist = db.execute_one(
            "SELECT id FROM wishlists WHERE id = %s AND user_id = %s",
            (wishlist_id, user['id'])
        )
        if not wishlist:
            return False, "القائمة غير موجودة أو لا تملكها"

        # البحث عن المنتج
        product = db.execute_one(
            "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_name,)
        )
        if not product:
            return False, "المنتج غير موجود في قاعدة البيانات. يرجى تحليله أولاً."

        # إضافة المنتج للقائمة
        db.execute_query(
            """INSERT INTO wishlist_items (wishlist_id, product_id, note)
               VALUES (%s, %s, %s)
               ON CONFLICT (wishlist_id, product_id) DO NOTHING""",
            (wishlist_id, product['id'], note)
        )

        return True, product_name
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة منتج للقائمة: {e}")
        return False, str(e)


def get_wishlist_items(telegram_id, wishlist_id):
    """جلب عناصر قائمة رغبات معينة"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return None

        # التحقق من الملكية أو العمومية
        wishlist = db.execute_one(
            """SELECT w.id, w.name, w.description FROM wishlists w
               WHERE w.id = %s AND (w.user_id = %s OR w.is_public = TRUE)""",
            (wishlist_id, user['id'])
        )
        if not wishlist:
            return None

        query = """
            SELECT p.product_name, p.score, p.sell_price, p.recommendation, wi.note, wi.added_at
            FROM wishlist_items wi
            JOIN products p ON wi.product_id = p.id
            WHERE wi.wishlist_id = %s
            ORDER BY wi.added_at DESC
        """
        results = db.execute_query(query, (wishlist_id,), fetch=True)

        return {
            "wishlist": dict(wishlist),
            "items": [dict(row) for row in results]
        }
    except Exception as e:
        logger.error(f"❌ خطأ في جلب عناصر القائمة: {e}")
        return None


def delete_wishlist(telegram_id, wishlist_id):
    """حذف قائمة رغبات"""
    try:
        user = db.execute_one(
            "SELECT id FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        if not user:
            return False

        db.execute_query(
            "DELETE FROM wishlists WHERE id = %s AND user_id = %s",
            (wishlist_id, user['id'])
        )
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حذف القائمة: {e}")
        return False


def remove_from_wishlist(telegram_id, wishlist_id, product_name):
    """حذف منتج من قائمة رغبات"""
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
            """DELETE FROM wishlist_items 
               WHERE wishlist_id = %s AND product_id = %s""",
            (wishlist_id, product['id'])
        )
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حذف منتج من القائمة: {e}")
        return False