MARGIN_BONUS = (
    (300, 20),
    (200, 15),
    (100, 10),
    (50, 5),
)

COMPETITION_BONUS = {
    "منخفضة": 15,
    "متوسطة": 8,
    "عالية": 2,
}


def calculate_hunter_score(
    ai_score,
    heat_score,
    margin,
    competition,
    product_power,
    google_trend
):

    score = 0

    # =========================
    # AI Score
    # =========================

    score += ai_score * 4

    # =========================
    # Heat Score
    # =========================

    score += heat_score * 2

    # =========================
    # Margin Bonus
    # =========================

    for limit, bonus in MARGIN_BONUS:
        if margin >= limit:
            score += bonus
            break

    # =========================
    # Competition
    # =========================

    score += COMPETITION_BONUS.get(
        competition,
        0
    )

    # =========================
    # Product Power
    # =========================

    score += product_power * 2

    # =========================
    # Google Trend
    # =========================

    score += google_trend / 5

    # =========================
    # Limit
    # =========================

    score = min(score, 100)

    return round(score, 1)