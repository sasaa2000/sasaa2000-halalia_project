"""
حلالية - إدارة تنبيهات الأسعار
"""

import logging
from backend.db import db

logger = logging.getLogger(__name__)


def create_price_alert(telegram_id, product_name, target_price):
    """إنشاء تنبيه سعر جديد"""
    try:
        # 1. الحصول على معرف المستخدم
        user = db.execute_one("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        if not user:
            return False, "no_user", "المستخدم غير موجود"

        # 2. الحصول على معرف المنتج وسعره الحالي
        product = db.execute_one(
            "SELECT id, sell_price FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_name,)
        )
        if not product:
            return False, "not_found", "المنتج غير موجود في قاعدة البيانات. يرجى تحليله أولاً."

        current_price = float(product['sell_price'] or 0)
        product_id = product['id']

        # 3. التحقق مما إذا كان السعر الحالي بالفعل أقل من أو يساوي السعر المستهدف
        if current_price <= target_price:
            return True, "already_lower", current_price

        # 4. التحقق من وجود تنبيه نشط مسبقاً لنفس المنتج ونفس المستخدم
        existing_alert = db.execute_one(
            """SELECT id FROM price_alerts 
               WHERE user_id = %s AND product_id = %s AND is_active = TRUE""",
            (user['id'], product_id)
        )

        if existing_alert:
            # تحديث السعر المستهدف إذا كان موجوداً
            db.execute_query(
                "UPDATE price_alerts SET target_price = %s WHERE id = %s",
                (target_price, existing_alert['id'])
            )
            return True, "updated", target_price
        else:
            # إنشاء تنبيه جديد
            db.execute_query(
                """INSERT INTO price_alerts (user_id, product_id, target_price) 
                   VALUES (%s, %s, %s)""",
                (user['id'], product_id, target_price)
            )
            return True, "created", target_price

    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء تنبيه السعر: {e}")
        return False, "error", str(e)


def get_user_alerts(telegram_id):
    """جلب جميع تنبيهات المستخدم النشطة"""
    try:
        user = db.execute_one("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        if not user:
            return []

        query = """
            SELECT p.product_name, a.target_price, p.sell_price as current_price, a.created_at
            FROM price_alerts a
            JOIN products p ON a.product_id = p.id
            WHERE a.user_id = %s AND a.is_active = TRUE
            ORDER BY a.created_at DESC
        """
        results = db.execute_query(query, (user['id'],), fetch=True)
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"❌ خطأ في جلب تنبيهات المستخدم: {e}")
        return []


def delete_alert(telegram_id, product_name):
    """حذف تنبيه سعر محدد"""
    try:
        user = db.execute_one("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        if not user:
            return False

        product = db.execute_one(
            "SELECT id FROM products WHERE LOWER(product_name) = LOWER(%s)",
            (product_name,)
        )
        if not product:
            return False

        db.execute_query(
            """UPDATE price_alerts SET is_active = FALSE 
               WHERE user_id = %s AND product_id = %s""",
            (user['id'], product['id'])
        )
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حذف تنبيه السعر: {e}")
        return False