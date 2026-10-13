def calculate_pricing(
    ai_score,
    product_power,
    competition,
    virality
):

    cost_price = 20

    if ai_score >= 9:
        multiplier = 3.2

    elif ai_score >= 7:
        multiplier = 2.8

    elif ai_score >= 5:
        multiplier = 2.2

    elif ai_score >= 3:
        multiplier = 1.6

    else:
        multiplier = 1.2

    # قوة المنتج

    if product_power >= 8:
        multiplier += 0.8

    elif product_power >= 6:
        multiplier += 0.5

    elif product_power >= 4:
        multiplier += 0.3

    # المنافسة

    if competition == "عالية":
        multiplier -= 0.4

    elif competition == "متوسطة":
        multiplier -= 0.2

    # الانتشار

    if virality == "مرتفع":
        multiplier += 0.5

    sell_price = round(cost_price * multiplier, 2)

    profit = round(sell_price - cost_price, 2)

    margin = round((profit / cost_price) * 100, 1)

    if margin >= 150:
        profitability = "ممتازة"

    elif margin >= 80:
        profitability = "جيدة"

    elif margin >= 40:
        profitability = "متوسطة"

    else:
        profitability = "ضعيفة"

    return {
        "cost_price": cost_price,
        "sell_price": sell_price,
        "profit": profit,
        "margin": margin,
        "profitability": profitability
    }