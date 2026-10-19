def rank_product(
    ai_score: float,
    heat_score: float,
    margin: float,
    competition,  # يمكن أن يكون نص أو رقم
    google_trend: float
) -> str:
    """
    جسر بين hunter_pipeline (أرقام) و ProductRanker (كائنات).
    
    تحسب rank (A/B/C/D) بناءً على 5 مؤشرات.
    """
    # تحويل competition من نص إلى رقم إذا لزم الأمر
    if isinstance(competition, str):
        competition_map = {
            "عالية": 8,
            "متوسطة": 5,
            "منخفضة": 2,
            "high": 8,
            "medium": 5,
            "low": 2
        }
        competition_value = competition_map.get(competition.lower(), 5)
    else:
        competition_value = competition
    
    # متوسط مرجح بسيط
    score = (
        ai_score * 0.3 +
        heat_score * 0.2 +
        margin * 0.2 +
        (10 - competition_value) * 0.15 +  # competition منخفض = أفضل
        google_trend * 0.15
    )
    
    if score >= 7.5:
        return "A"
    elif score >= 6.0:
        return "B"
    elif score >= 4.5:
        return "C"
    else:
        return "D"