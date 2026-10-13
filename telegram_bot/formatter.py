SEPARATOR = "━━━━━━━━━━━━━━━━━━"


def format_product(data):
    g = data.get

    return (
        f"📦 المنتج: {g('product_name', '-')}\n"
        f"{SEPARATOR}\n"

        f"🤖 AI Score: {g('score', '-')}/10\n"
        f"🎯 Hunter Score: {g('hunter_score', '-')}/100\n"
        f"🏆 Rank: {g('rank', '-')}\n\n"

        f"🔥 الطلب: {g('demand', '-')}\n"
        f"📈 Viral Score: {g('virality', '-')}\n"
        f"🧠 النيتش: {g('niche', '-')}\n\n"

        f"🌡 Heat Score: {g('heat_score', '-')}\n"
        f"📊 Google Trend: {g('google_trend', '-')}/100\n"
        f"📈 Trend Direction: {g('trend_direction', '-')}\n"
        f"🔥 Heat Level: {g('heat_level', '-')}\n\n"

        f"🚀 Winning Chance: {g('winning_probability', '-')}\n"
        f"⚔️ المنافسة: {g('competition', '-')}\n"
        f"🚚 الشحن: {g('shipping', '-')}\n"
        f"💰 الربحية: {g('profitability', '-')}\n\n"

        f"💸 سعر الشراء: {g('cost_price', '-')} $\n"
        f"💲 سعر البيع: {g('sell_price', '-')} $\n"
        f"📈 الهامش: {g('margin', '-')}%\n"
        f"💵 الربح: {g('profit', '-')} $\n"

        f"{SEPARATOR}\n"
        f"🎯 {g('recommendation', '-')}"
    )


def format_compare(result1, result2):

    winner = max(
        (result1, result2),
        key=lambda x: x.get("hunter_score", 0)
    )

    return (
        "⚖️ مقارنة بين منتجين\n"
        f"{SEPARATOR}\n\n"

        f"📦 {result1.get('product_name', '-')}\n"
        f"🤖 AI : {result1.get('score', '-')}/10\n"
        f"🎯 Hunter : {result1.get('hunter_score', '-')}/100\n"
        f"💰 Profit : {result1.get('profit', '-')} $\n\n"

        f"📦 {result2.get('product_name', '-')}\n"
        f"🤖 AI : {result2.get('score', '-')}/10\n"
        f"🎯 Hunter : {result2.get('hunter_score', '-')}/100\n"
        f"💰 Profit : {result2.get('profit', '-')} $\n\n"

        "🏆 الفائز\n"
        f"{winner.get('product_name', '-')}"
    )


def format_saved(products):

    if not products:
        return "📭 لا توجد منتجات محفوظة."

    lines = [
        "🏆 أفضل المنتجات المحفوظة",
        SEPARATOR,
        ""
    ]

    for index, product in enumerate(products, start=1):
        lines.extend([
            f"{index}. {product.get('product_name', '-')}",
            f"🎯 Hunter : {product.get('hunter_score', '-')}/100",
            f"🤖 AI : {product.get('score', '-')}/10",
            f"🏆 Rank : {product.get('rank', '-')}",
            f"💰 Profit : {product.get('profit', '-')} $",
            ""
        ])

    return "\n".join(lines)


def format_hunt(products):

    if not products:
        return "❌ لا توجد منتجات."

    lines = [
        "🔥 أفضل المنتجات المكتشفة",
        SEPARATOR,
        ""
    ]

    for index, product in enumerate(products, start=1):
        lines.extend([
            f"{index}. {product.get('product_name', '-')}",
            f"🎯 Hunter : {product.get('hunter_score', '-')}/100",
            f"🏆 Rank : {product.get('rank', '-')}",
            f"💰 Profit : {product.get('profit', '-')} $",
            ""
        ])

    return "\n".join(lines)