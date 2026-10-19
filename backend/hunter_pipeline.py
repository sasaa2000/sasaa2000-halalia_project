from backend.product_intelligence import calculate_product_power
from backend.advanced_ai import analyze_advanced
from backend.trend_engine import predict_trend
from backend.competition_engine import calculate_competition
from backend.hunter_score import calculate_hunter_score
from backend.ranking import rank_product as calculate_rank
from backend.winning_engine import calculate_winning_probability

from backend.market_intelligence import analyze_market



def run_pipeline(product):

    name = product["name"]
    reviews = product["reviews"]
    rating = product["rating"]
    price = product["price"]

    power = calculate_product_power(
        product_name=name,
        reviews=reviews,
        rating=rating,
        price=price
    )

    ai = analyze_advanced(
        product_name=name,
        product_power=power
    )

    trend = predict_trend(name)

    competition = calculate_competition(
        product_name=name,
        niche=trend["niche"],
        google_trend=trend["google_trend"],
        keyword_bonus=ai["keyword_bonus"]
    )

    market = analyze_market(
        product_name=name,
        niche=trend["niche"],
        google_trend=trend["google_trend"],
        competition=competition
    )

    rank = calculate_rank(
        ai_score=ai["score"],
        heat_score=trend["heat_score"],
        margin=ai["margin"],
        competition=competition,
        google_trend=trend["google_trend"]
    )

    winning_probability = calculate_winning_probability(
        rank=rank,
        competition=competition,
        heat_score=trend["heat_score"]
    )

    hunter_score = calculate_hunter_score(
        ai_score=ai["score"],
        heat_score=trend["heat_score"],
        margin=ai["margin"],
        competition=competition,
        google_trend=trend["google_trend"],
        product_power=power
    )

    return {
        **ai,
        **trend,
        **market,
        "product_power": power,
        "competition": competition,
        "rank": rank,
        "winning_probability": winning_probability,
        "hunter_score": hunter_score,
        "reviews": reviews,
        "rating": rating,
        "amazon_price": price
    }


def run_custom_pipeline(
    product_name,
    reviews,
    rating,
    price
):

    product = {
        "name": product_name,
        "reviews": reviews,
        "rating": rating,
        "price": price
    }

    return run_pipeline(product)