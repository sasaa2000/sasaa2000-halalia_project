# ==========================================
# Market Score Engine
# Version 1.0
# ==========================================


def calculate_market_score(
    google_trend,
    competition,
    novelty_score,
    market_saturation,
):
    score = 0

    # Google Trend

    score += google_trend * 0.40

    # Novelty

    score += novelty_score * 0.30

    # Saturation

    score += (100 - market_saturation) * 0.20

    # Competition

    if competition == "منخفضة":
        score += 10

    elif competition == "متوسطة":
        score += 5

    return round(min(score, 100), 1)