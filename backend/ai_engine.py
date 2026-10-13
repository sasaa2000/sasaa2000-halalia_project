# =========================================
# 🔥 كلمات قوية ترفع التقييم
# =========================================

TRENDING_KEYWORDS = {
    "smart": 2,
    "led": 1.5,
    "wireless": 2,
    "portable": 1.5,
    "mini": 1,
    "beauty": 2,
    "fitness": 2,
    "pet": 1.5,
    "car": 1,
    "kitchen": 1,
    "gaming": 2,
    "baby": 1.5
}


# =========================================
# ⚠️ كلمات مشبعة تقلل التقييم
# =========================================

SATURATED_KEYWORDS = {
    "iphone": -2,
    "case": -1.5,
    "cover": -1,
    "charger": -1,
    "cable": -1
}


# =========================================
# 🧠 التحليل الذكي
# =========================================

def analyze_product_ai(product_name: str):

    name = product_name.lower()

    score = 5

    demand = "متوسط"

    competition = "متوسطة"

    shipping = "سهل"

    # =====================================
    # 🔥 فحص الكلمات القوية
    # =====================================

    for keyword, value in TRENDING_KEYWORDS.items():

        if keyword in name:
            score += value

    # =====================================
    # ⚠️ فحص السوق المشبع
    # =====================================

    for keyword, value in SATURATED_KEYWORDS.items():

        if keyword in name:
            score += value
            competition = "عالية"

    # =====================================
    # 📈 تحديد الطلب
    # =====================================

    if score >= 9:
        demand = "مرتفع جداً"

    elif score >= 7:
        demand = "مرتفع"

    elif score >= 5:
        demand = "متوسط"

    else:
        demand = "ضعيف"

    # =====================================
    # 🚚 تقييم الشحن
    # =====================================

    heavy_products = [
        "table",
        "chair",
        "desk"
    ]

    for item in heavy_products:

        if item in name:
            shipping = "صعب"

    # =====================================
    # 💰 التسعير
    # =====================================

    cost_price = 20

    multiplier = 2 + (score / 10)

    sell_price = round(cost_price * multiplier, 2)

    profit = round(sell_price - cost_price, 2)

    margin = round((profit / cost_price) * 100, 1)

    # =====================================
    # 💵 تقييم الربحية
    # =====================================

    if margin >= 150:
        profitability = "ممتازة"

    elif margin >= 100:
        profitability = "جيدة جداً"

    elif margin >= 70:
        profitability = "جيدة"

    else:
        profitability = "ضعيفة"

    # =====================================
    # 🎯 التوصية النهائية
    # =====================================

    if score >= 9:
        recommendation = "منتج قوي جداً للبيع 🚀"

    elif score >= 7:
        recommendation = "منتج ممتاز ويستحق التجربة ✅"

    elif score >= 5:
        recommendation = "يحتاج اختبار ⚖️"

    else:
        recommendation = "السوق صعب حالياً ❌"

    # =====================================
    # 📦 النتيجة النهائية
    # =====================================

    return {
        "product_name": product_name,
        "score": round(score, 1),
        "demand": demand,
        "competition": competition,
        "shipping": shipping,
        "profitability": profitability,
        "recommendation": recommendation,
        "cost_price": cost_price,
        "sell_price": sell_price,
        "profit": profit,
        "margin": margin
    }