GENERIC_PRODUCTS = [
    "watch",
    "mouse",
    "charger",
    "speaker",
    "headphone",
    "lamp",
    "case",
]

HOT_NICHES = {
    "pet",
    "baby",
    "beauty",
    "fitness",
}


def calculate_competition(
    product_name,
    niche,
    google_trend,
    keyword_bonus=0,
):
    name = product_name.lower()
    score = 0

    # =========================
    # Google Trend
    # =========================
    if google_trend >= 70:
        score += 4
    elif google_trend >= 50:
        score += 3
    elif google_trend >= 30:
        score += 2

    # =========================
    # Generic Products
    # =========================
    if any(word in name for word in GENERIC_PRODUCTS):
        score += 3

    # =========================
    # Keyword Bonus
    # =========================
    score += keyword_bonus

    # =========================
    # Niche Effect
    # =========================
    if niche in HOT_NICHES:
        score -= 3
    elif niche in ("smart", "gaming"):
        score += 2

    # =========================
    # Competition Level
    # =========================
    if score >= 8:
        competition = "عالية"
    elif score >= 4:
        competition = "متوسطة"
    else:
        competition = "منخفضة"

    return competition