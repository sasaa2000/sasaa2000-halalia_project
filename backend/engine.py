def pricing_analysis(product_name: str):
    base_prices = {
        "led facial mask": 25,
        "power bank": 15,
        "yoga mat": 10
    }

    key = product_name.lower()
    cost = base_prices.get(key, 20)

    sell_price = round(cost * 1.9, 2)
    profit = round(sell_price - cost, 2)
    margin = round((profit / cost) * 100, 1)

    return {
        "cost_price": cost,
        "sell_price": sell_price,
        "profit": profit,
        "margin": margin
    }


def analyze_product(product_name: str):
    pricing = pricing_analysis(product_name)

    return {
        "product": product_name,
        "score": 9.0,
        "demand": "مرتفع",
        "competition": "متوسطة",
        "cost_price": pricing["cost_price"],
        "sell_price": pricing["sell_price"],
        "profit": pricing["profit"],
        "margin": pricing["margin"],
    }