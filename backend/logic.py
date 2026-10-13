def analyze_product_logic(product: str, country: str, platform: str):
    category = classify_product(product)
    scores = calculate_score(category)

    total_score = sum(scores.values())
    reasons = []

    reasons.append(f"تصنيف المنتج: {category}")
    reasons.append(f"الطلب المتوقع: {scores['demand']}/5")
    reasons.append(f"هامش الربح: {scores['profit']}/5")
    reasons.append(f"المنافسة: {abs(scores['competition'])}/5")
    reasons.append(f"سهولة البيع: {scores['ease']}/5")

    # القرار النهائي
    if total_score >= 6:
        verdict = "ابدأ الآن"
        risk = "متوسطة"
        recommendation = "ابدأ باختبار سريع بإعلانات منخفضة الميزانية"
        price_range = "مرتفع نسبيًا"
    elif total_score >= 4:
        verdict = "اختبر بحذر"
        risk = "مرتفعة"
        recommendation = "اختبر المنتج مع دراسة المنافسين جيدًا"
        price_range = "متوسط"
    else:
        verdict = "تجنّب المنتج"
        risk = "عالية"
        recommendation = "لا يُنصح بالبدء بهذا المنتج حاليًا"
        price_range = "غير مناسب"

    action_plan = generate_action_plan(verdict, category)
    return {
        "score": total_score,
        "verdict": verdict,
        "reasons": reasons,
        "price_range": price_range,
        "risk": risk,
        "recommendation": recommendation,
        "action_plan": action_plan
    }

    

