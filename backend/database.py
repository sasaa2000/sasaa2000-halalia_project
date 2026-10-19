"""
حلالية - إدارة المنتجات في قاعدة البيانات PostgreSQL
"""

import json
import logging
from backend.db import db
from datetime import datetime

logger = logging.getLogger(__name__)


def load_products():
    """تحميل جميع المنتجات من قاعدة البيانات"""
    try:
        query = "SELECT * FROM products ORDER BY created_at DESC"
        results = db.execute_query(query, fetch=True)

        products = []
        for row in results:
            product = dict(row)
            # تحويل JSONB إلى dict
            if product.get('amazon_market'):
                product['amazon_market'] = dict(product['amazon_market'])
            products.append(product)

        logger.info(f" تم تحميل {len(products)} منتج من قاعدة البيانات")
        return products
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل المنتجات: {e}")
        return []


def save_product(product_data):
    """حفظ أو تحديث منتج في قاعدة البيانات"""
    try:
        product_name = product_data.get("product_name", "").strip()

        # التحقق من وجود المنتج مسبقاً
        check_query = "SELECT id, score FROM products WHERE LOWER(product_name) = LOWER(%s)"
        existing = db.execute_one(check_query, (product_name,))

        if existing:
            # تحديث إذا كانت الدرجة الجديدة أعلى
            if product_data.get("score", 0) > existing['score']:
                update_query = """
                    UPDATE products SET 
                        score = %s, hunter_score = %s, rank = %s, recommendation = %s,
                        sell_price = %s, cost_price = %s, profit = %s, margin = %s,
                        demand = %s, competition = %s, shipping = %s, profitability = %s,
                        heat_score = %s, heat_level = %s, google_trend = %s, trend_direction = %s,
                        market_saturation = %s, novelty_score = %s, seasonality = %s,
                        repeat_purchase = %s, emotional_buying = %s, long_term_potential = %s,
                        market_score = %s, product_power = %s, winning_probability = %s,
                        reviews_count = %s, rating = %s, niche = %s,
                        amazon_market = %s::jsonb, keyword_bonus = %s, matched_keywords = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """
                db.execute_query(update_query, (
                    product_data.get("score"),
                    product_data.get("hunter_score"),
                    product_data.get("rank"),
                    product_data.get("recommendation"),
                    product_data.get("sell_price"),
                    product_data.get("cost_price"),
                    product_data.get("profit"),
                    product_data.get("margin"),
                    product_data.get("demand"),
                    product_data.get("competition"),
                    product_data.get("shipping"),
                    product_data.get("profitability"),
                    product_data.get("heat_score"),
                    product_data.get("heat_level"),
                    product_data.get("google_trend"),
                    product_data.get("trend_direction"),
                    product_data.get("market_saturation"),
                    product_data.get("novelty_score"),
                    product_data.get("seasonality"),
                    product_data.get("repeat_purchase"),
                    product_data.get("emotional_buying"),
                    product_data.get("long_term_potential"),
                    product_data.get("market_score"),
                    product_data.get("product_power"),
                    product_data.get("winning_probability"),
                    product_data.get("reviews", 0),
                    product_data.get("rating", 0),
                    product_data.get("niche"),
                    json.dumps(product_data.get("amazon_market", {})),
                    product_data.get("keyword_bonus", 0),
                    product_data.get("matched_keywords", []),
                    existing['id']
                ))
                logger.info(f"🔄 تم تحديث المنتج: {product_name}")
        else:
            # إدخال منتج جديد
            insert_query = """
                INSERT INTO products (
                    product_name, score, hunter_score, rank, recommendation,
                    sell_price, cost_price, profit, margin,
                    demand, competition, shipping, profitability,
                    heat_score, heat_level, google_trend, trend_direction,
                    market_saturation, novelty_score, seasonality,
                    repeat_purchase, emotional_buying, long_term_potential,
                    market_score, product_power, winning_probability,
                    reviews_count, rating, niche,
                    amazon_market, keyword_bonus, matched_keywords
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s::jsonb, %s, %s
                )
                RETURNING id
            """
            db.execute_query(insert_query, (
                product_data.get("product_name"),
                product_data.get("score"),
                product_data.get("hunter_score"),
                product_data.get("rank"),
                product_data.get("recommendation"),
                product_data.get("sell_price"),
                product_data.get("cost_price"),
                product_data.get("profit"),
                product_data.get("margin"),
                product_data.get("demand"),
                product_data.get("competition"),
                product_data.get("shipping"),
                product_data.get("profitability"),
                product_data.get("heat_score"),
                product_data.get("heat_level"),
                product_data.get("google_trend"),
                product_data.get("trend_direction"),
                product_data.get("market_saturation"),
                product_data.get("novelty_score"),
                product_data.get("seasonality"),
                product_data.get("repeat_purchase"),
                product_data.get("emotional_buying"),
                product_data.get("long_term_potential"),
                product_data.get("market_score"),
                product_data.get("product_power"),
                product_data.get("winning_probability"),
                product_data.get("reviews", 0),
                product_data.get("rating", 0),
                product_data.get("niche"),
                json.dumps(product_data.get("amazon_market", {})),
                product_data.get("keyword_bonus", 0),
                product_data.get("matched_keywords", [])
            ))
            logger.info(f"✅ تم حفظ منتج جديد: {product_name}")

        return True
    except Exception as e:
        logger.error(f" خطأ في حفظ المنتج: {e}")
        return False


def get_product_by_name(product_name):
    """البحث عن منتج بالاسم"""
    try:
        query = "SELECT * FROM products WHERE LOWER(product_name) = LOWER(%s)"
        return db.execute_one(query, (product_name,))
    except Exception as e:
        logger.error(f"❌ خطأ في البحث عن المنتج: {e}")
        return None


def get_top_products(limit=10):
    """الحصول على أفضل المنتجات"""
    try:
        query = "SELECT * FROM products ORDER BY score DESC LIMIT %s"
        return db.execute_query(query, (limit,), fetch=True)
    except Exception as e:
        logger.error(f"❌ خطأ في جلب أفضل المنتجات: {e}")
        return []


def delete_product(product_name):
    """حذف منتج من قاعدة البيانات"""
    try:
        query = "DELETE FROM products WHERE LOWER(product_name) = LOWER(%s)"
        db.execute_query(query, (product_name,))
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حذف المنتج: {e}")
        return False