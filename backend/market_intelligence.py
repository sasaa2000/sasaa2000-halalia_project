from backend.market_score_engine import calculate_market_score
from backend.amazon_market import get_amazon_market_data

# ==========================================
# AI Product Hunter
# Market Intelligence Engine
# Version 2.0
# ==========================================

SMART_WORDS = [
    "ai",
    "smart",
    "automatic",
    "wireless",
    "portable",
    "mini",
    "magnetic",
    "rechargeable",
    "usb",
    "foldable",
    "digital"
]

GENERIC_PRODUCTS = [
    "case",
    "mouse",
    "watch",
    "charger",
    "speaker",
    "lamp",
    "cable",
    "bottle"
]

SATURATED_PRODUCTS = [
    "iphone case",
    "phone case",
    "usb cable",
    "charger",
    "mouse",
    "keyboard",
    "speaker",
    "headphone",
    "watch",
    "lamp"
]

EVERGREEN_NICHES = [
    "pet",
    "baby",
    "beauty",
    "fitness",
    "home",
    "kitchen"
]

EMOTIONAL_NICHES = [
    "pet",
    "baby",
    "beauty"
]

REPEAT_NICHES = [
    "pet",
    "beauty",
    "fitness"
]

SEASONAL_WORDS = [
    "christmas",
    "winter",
    "summer",
    "halloween",
    "ramadan",
    "eid"
]


# ===================================================
# Market Saturation
# ===================================================

def calculate_market_saturation(
    name,
    competition,
    google_trend
):

    score = 20

    if competition == "عالية":
        score += 40

    elif competition == "متوسطة":
        score += 20

    if google_trend >= 70:
        score += 20

    elif google_trend >= 50:
        score += 10

    for word in GENERIC_PRODUCTS:

        if word in name:
            score += 20

    for word in SATURATED_PRODUCTS:

        if word in name:
            score += 20

    return min(score, 100)


# ===================================================
# Novelty
# ===================================================

def calculate_novelty(name):

    score = 40

    for word in SMART_WORDS:

        if word in name:
            score += 8

    return min(score, 100)


# ===================================================
# Seasonality
# ===================================================

def calculate_seasonality(name):

    for word in SEASONAL_WORDS:

        if word in name:
            return "Seasonal"

    return "Evergreen"


# ===================================================
# Repeat Purchase
# ===================================================

def calculate_repeat_purchase(niche):

    if niche in REPEAT_NICHES:
        return "High"

    if niche in EVERGREEN_NICHES:
        return "Medium"

    return "Low"


# ===================================================
# Emotional Buying
# ===================================================

def calculate_emotional_buying(niche):

    if niche in EMOTIONAL_NICHES:
        return "High"

    return "Low"


# ===================================================
# Long Term Potential
# ===================================================

def calculate_long_term(
    seasonality,
    saturation
):

    if seasonality == "Evergreen" and saturation < 60:
        return "High"

    elif saturation < 80:
        return "Medium"

    return "Low"


# ===================================================
# Market Score
# ===================================================

def calculate_market_score(
    saturation,
    novelty,
    google_trend
):

    score = (
        novelty * 0.40 +
        google_trend * 0.30 +
        (100 - saturation) * 0.30
    )

    return round(score, 1)


# ===================================================
# Main Function
# ===================================================

def analyze_market(
    product_name,
    niche,
    google_trend,
    competition
):

    name = product_name.lower()

    amazon = get_amazon_market_data(product_name)

    market_saturation = calculate_market_saturation(
        name,
        competition,
        google_trend
    )

    novelty_score = calculate_novelty(name)

    seasonality = calculate_seasonality(name)

    repeat_purchase = calculate_repeat_purchase(niche)

    emotional_buying = calculate_emotional_buying(niche)

    long_term_potential = calculate_long_term(
        seasonality,
        market_saturation
    )

    market_score = calculate_market_score(
        saturation=market_saturation,
        novelty=novelty_score,
        google_trend=google_trend
    )

    return {

        "market_saturation": market_saturation,

        "novelty_score": novelty_score,

        "seasonality": seasonality,

        "repeat_purchase": repeat_purchase,

        "emotional_buying": emotional_buying,

        "long_term_potential": long_term_potential,

        "market_score": market_score,

        "amazon_market": amazon,
    }