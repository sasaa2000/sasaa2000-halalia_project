def pricing_analysis(product_name: str) -> dict:
    base_prices = {
        "led facial mask": 25,
        "power bank": 15,
        "yoga mat": 10
    }

    key = product_name.lower().strip()
    cost = base_prices.get(key)

    if cost is None:
        raise ValueError(f"Product '{product_name}' not found")

    sell_price = round(cost * 1.9, 2)
    profit = round(sell_price - cost, 2)
    margin = round((profit / sell_price) * 100, 1)  # ✅ Gross Margin

    return {
        "cost_price": cost,
        "sell_price": sell_price,
        "profit": profit,
        "margin_percent": margin  # أوضح في التسمية
    }


def analyze_product(product_name: str) -> dict:
    return {
        "product": product_name,
        "pricing": pricing_analysis(product_name),
    }