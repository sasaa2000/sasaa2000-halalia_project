print("ADVANCED_AI FILE LOADED")
print(__file__)

from backend.pricing_engine import calculate_pricing
from backend.product_categories import get_category_bonus
from backend.product_keywords import get_keyword_bonus
from backend.competition_engine import calculate_competition
from backend.category_detector import detect_category

TREND_KEYWORDS = [
    "smart",
    "led",
    "portable",
    "wireless",
    "pet",
    "fitness",
    "mini",
    "automatic",
    "rechargeable",
    "usb"
]

BAD_PRODUCTS = [
    "iphone case",
    "supplement",
    "protein",
    "watch classic",
    "fake"
]


def analyze_advanced(product_name, product_power):

    name = product_name.lower()

    score = 0
    trend_score = 0

    for word in TREND_KEYWORDS:
        if word in name:
            trend_score += 1

    score += trend_score

    keyword_data = get_keyword_bonus(product_name)

    score += keyword_data["keyword_bonus"]

    category = detect_category(product_name)

    niche = category

    category_bonus = get_category_bonus(category)

    score += category_bonus

    score += product_power * 0.4

    for bad in BAD_PRODUCTS:
        if bad in name:
            score -= 4

    competition = calculate_competition(
        product_name=product_name,
        niche=niche,
        google_trend=0,
        keyword_bonus=keyword_data["keyword_bonus"]
    )

    shipping = "سهل"

    if "furniture" in name:
        shipping = "صعب"
        score -= 2

    if score > 10:
        score = 10

    if score < 1:
        score = 1

    virality = "ضعيف"

    if trend_score >= 2:
        virality = "مرتفع"

    if score >= 8:
        demand = "مرتفع جداً"

    elif score >= 6:
        demand = "مرتفع"

    else:
        demand = "متوسط"

    pricing = calculate_pricing(
        ai_score=score,
        product_power=product_power,
        competition=competition,
        virality=virality
    )

    if score >= 8:
        recommendation = "منتج ممتاز ويستحق التجربة ✅"

    elif score >= 6:
        recommendation = "منتج جيد ويستحق الاختبار ⚖️"

    else:
        recommendation = "غير مفضل حالياً ❌"

    return {

        "product_name": product_name,

        "score": round(score, 1),

        "keyword_bonus": keyword_data["keyword_bonus"],

        "matched_keywords": keyword_data["matched_keywords"],

        "niche": niche,

        "demand": demand,

        "competition": competition,

        "shipping": shipping,

        "virality": virality,

        **pricing,

        "recommendation": recommendation

    }