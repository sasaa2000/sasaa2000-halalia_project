MARGIN_BONUS = (
    (150, 3),
    (100, 2),
    (50, 1),
)

GOOGLE_TREND_BONUS = (
    (70, 3),
    (50, 2),
    (30, 1),
)

COMPETITION_PENALTY = {
    "عالية": 5,
    "متوسطة": 2,
}

RANK_LEVELS = (
    (22, "⭐ ELITE"),
    (18, "🏆 A+"),
    (14, "🥇 A"),
    (10, "🥈 B"),
    (6, "🥉 C"),
)


def calculate_rank(
    score,
    heat,
    margin,
    competition,
    google_trend=0,
    trend_direction="غير معروف"
):

    total = score + heat

    # =========================
    # Margin Bonus
    # =========================

    for limit, bonus in MARGIN_BONUS:
        if margin >= limit:
            total += bonus
            break

    # =========================
    # Google Trend Bonus
    # =========================

    for limit, bonus in GOOGLE_TREND_BONUS:
        if google_trend >= limit:
            total += bonus
            break

    # =========================
    # Trend Direction
    # =========================

    if "صاعد" in trend_direction:
        total += 2

    elif "هابط" in trend_direction:
        total -= 2

    # =========================
    # Competition
    # =========================

    total -= COMPETITION_PENALTY.get(competition, 0)

    # =========================
    # Safety
    # =========================

    total = max(total, 0)

    # =========================
    # Final Rank
    # =========================

    for limit, rank in RANK_LEVELS:
        if total >= limit:
            return rank

    return "❌ D"