from backend.google_trends import get_google_trend_data
from backend.heat_engine import get_heat_level
from backend.winning_engine import calculate_winning_probability


VIRAL_WORDS = [
    "tiktok",
    "viral",
    "smart",
    "mini",
    "portable",
    "automatic",
    "wireless",
    "rechargeable",
    "usb"
]

PET_WORDS = [
    "pet",
    "cat",
    "dog",
    "kitten",
    "puppy",
    "animal"
]

BEAUTY_WORDS = [
    "beauty",
    "makeup",
    "cosmetic",
    "skincare"
]

FITNESS_WORDS = [
    "fitness",
    "gym",
    "workout"
]


def predict_trend(product_name):

    name = product_name.lower()

    heat_score = 0
    niche = "general"

    google_data = get_google_trend_data(product_name)

    google_score = google_data.get("google_trend", 0)
    trend_direction = google_data.get("trend_direction", "غير معروف")

    # Google Trend

    heat_score += google_score // 20

    # Niche

    if any(word in name for word in PET_WORDS):
        niche = "pet"
        heat_score += 3

    elif any(word in name for word in BEAUTY_WORDS):
        niche = "beauty"
        heat_score += 2

    elif any(word in name for word in FITNESS_WORDS):
        niche = "fitness"
        heat_score += 2

    elif "smart" in name:
        niche = "smart"
        heat_score += 2

    elif "gaming" in name:
        niche = "gaming"
        heat_score += 2

    elif "baby" in name:
        niche = "baby"
        heat_score += 2

    elif "kitchen" in name:
        niche = "kitchen"
        heat_score += 1

    elif "home" in name:
        niche = "home"
        heat_score += 1

    # Viral

    viral_count = sum(
        word in name
        for word in VIRAL_WORDS
    )

    heat_score += viral_count

    # Google Bonus

    if google_score >= 70:
        heat_score += 5

    elif google_score >= 50:
        heat_score += 3

    elif google_score >= 30:
        heat_score += 1

    heat_score = min(heat_score, 15)

    heat_level = get_heat_level(heat_score)

    return {
        "niche": niche,
        "heat_score": heat_score,
        "heat_level": heat_level,
        "google_trend": google_score,
        "trend_direction": trend_direction
    }

