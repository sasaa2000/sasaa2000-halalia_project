def analyze_product(product_name: str) -> dict:
    product_name = product_name.lower()

    if "mask" in product_name or "led" in product_name:
        return {
            "score": "8.2 / 10",
            "demand": "مرتفع",
            "competition": "متوسطة",
            "profit": "جيدة",
            "recommendation": "منتج قوي للتجربة"
        }

    return {
        "score": "6.5 / 10",
        "demand": "متوسط",
        "competition": "عالية",
        "profit": "ضعيفة",
        "recommendation": "يحتاج دراسة أعمق"
    }


