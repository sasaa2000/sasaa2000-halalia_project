def calculate_heat_score(
    niche,
    keyword_bonus,
    google_trend=0,
    trend_direction="غير معروف"
):

    score = 0

    # =====================
    # Niche Weight
    # =====================

    niche_weights = {

        "pet": 4,
        "smart": 3,
        "beauty": 3,
        "fitness": 3,
        "gaming": 2,
        "baby": 2,
        "kitchen": 1,
        "general": 0
    }

    score += niche_weights.get(
        niche,
        0
    )

    # =====================
    # Keyword Bonus
    # =====================

    score += keyword_bonus

    # =====================
    # Google Trends
    # =====================

    if google_trend >= 70:
        score += 5

    elif google_trend >= 50:
        score += 3

    elif google_trend >= 30:
        score += 2

    elif google_trend >= 10:
        score += 1

    # =====================
    # Trend Direction
    # =====================

    if "صاعد" in trend_direction:
        score += 2

    elif "هابط" in trend_direction:
        score -= 2

    if score < 0:
        score = 0

    return score


def get_heat_level(score):

    if score >= 12:
        return "🔥🔥🔥"

    elif score >= 6:
        return "🔥🔥"

    return "🔥"