def calculate_winning_probability(
    rank,
    competition,
    heat_score
):

    score = 0

    RANK_SCORES = {
        "⭐ ELITE": 4,
        "🏆 A+": 3,
        "🥇 A": 2,
        "🥈 B": 1,
    }

    COMPETITION_SCORES = {
        "منخفضة": 3,
        "متوسطة": 1,
    }

    score += RANK_SCORES.get(rank, 0)
    score += COMPETITION_SCORES.get(competition, 0)

    if heat_score >= 12:
        score += 4
    elif heat_score >= 8:
        score += 3
    elif heat_score >= 5:
        score += 2
    elif heat_score >= 3:
        score += 1

    if score >= 10:
        return "مرتفع جداً"
    elif score >= 7:
        return "مرتفع"
    elif score >= 4:
        return "متوسط"

    return "ضعيف"