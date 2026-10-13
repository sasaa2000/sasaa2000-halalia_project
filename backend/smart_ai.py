TREND_KEYWORDS = {
    "smart": 2,
    "led": 2,
    "portable": 2,
    "wireless": 2,
    "pet": 1.5,
    "fitness": 1.5,
    "kitchen": 1,
    "car": 1,
    "mini": 1,
    "beauty": 1.5,
}

BAD_KEYWORDS = {
    "iphone": -2,
    "case": -2,
    "cover": -2,
    "charger": -1,
}


def analyze_product_ai(product_name):

    name = product_name.lower()

    score = 5

    # 🔥 الكلمات القوية
    for word, value in TREND_KEYWORDS.items():
        if word in name:
            score += value

    # ❌ الكلمات السيئة
    for word, value in BAD_KEYWORDS.items():
        if word in name:
            score += value

    # منع تخطي الحدود
    score = max(1, min(score, 10))

    # =========================
    # 🔥 الطلب
    # =========================
    if score >= 8:
        demand = "مرتفع جداً"
    elif score >= 6:
        demand = "مرتفع"
    else:
        demand = "متوسط"

    # =========================
    # 🔥 المنافسة
    # =========================
    if "iphone" in name or "case" in name:
        competition = "عالية"
    else:
        competition = "متوسطة"

    # =========================
    # 🔥 الشحن
    # =========================
    if "glass" in name or "machine" in name:
        shipping = "صعب"
    else:
        shipping = "سهل"

    # =========================
    # 🔥 الأسعار
    # =========================
    cost_price = 20

    sell_price = round(cost_price * (1 + (score / 5)), 2)

    profit = round(sell_price - cost_price, 2)

    margin = round((profit / cost_price) * 100, 1)

    # =========================
    # 🔥 الربحية
    # =========================
    if margin >= 120:
        profitability = "ممتازة"
    elif margin >= 70:
        profitability = "جيدة"
    else:
        profitability = "ضعيفة"

    # =========================
    # 🔥 التوصية
    # =========================
    if score >= 8:
        recommendation = "منتج ممتاز ويستحق التجربة ✅"
    elif score >= 6:
        recommendation = "منتج جيد ويستحق الاختبار 🔥"
    else:
        recommendation = "غير مفضل حالياً ❌"

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