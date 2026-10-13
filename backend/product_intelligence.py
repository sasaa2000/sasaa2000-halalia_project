REVIEW_BONUS = (
    (5000, 3),
    (1000, 2),
    (100, 1),
)

RATING_BONUS = (
    (4.7, 3),
    (4.4, 2),
    (4.0, 1),
)

PROBLEM_WORDS = [
    "automatic",
    "smart",
    "tracker",
    "feeder",
    "cleaner",
    "security",
    "camera",
]

WOW_WORDS = [
    "ai",
    "smart",
    "mini",
    "portable",
    "wireless",
    "led",
]


def calculate_product_power(
    product_name,
    reviews=0,
    rating=0,
    price=0
):

    score = 0

    # =========================
    # Reviews
    # =========================

    for limit, bonus in REVIEW_BONUS:
        if reviews >= limit:
            score += bonus
            break

    # =========================
    # Rating
    # =========================

    for limit, bonus in RATING_BONUS:
        if rating >= limit:
            score += bonus
            break

    # =========================
    # Price
    # =========================

    if 20 <= price <= 80:
        score += 2

    elif 10 <= price <= 120:
        score += 1

    # =========================
    # Product Name
    # =========================

    name = product_name.lower()

    score += sum(
        word in name
        for word in PROBLEM_WORDS
    )

    score += sum(
        word in name
        for word in WOW_WORDS
    )

    score = min(score, 10)

    return score