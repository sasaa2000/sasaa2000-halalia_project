from backend.ranking.models import ProductScore
from backend.ranking.ranking_weights import RankingWeights


class ScoreCalculator:

    @staticmethod
    def calculate(product):

        score = ProductScore()

        # ======================================
        # Rating
        # ======================================

        rating = float(product.get("rating", 0))

        score.rating_score = (
            (rating / 5.0)
            * 100
            * RankingWeights.RATING
        )

        # ======================================
        # Reviews
        # ======================================

        reviews = int(product.get("reviews", 0))

        review_ratio = min(reviews, 1000) / 1000

        score.review_score = (
            review_ratio
            * 100
            * RankingWeights.REVIEWS
        )

        # ======================================
        # Price
        # ======================================

        price = float(product.get("price") or 0)

        if price > 0:

            price_ratio = min(price, 1000) / 1000

            score.price_score = (
                (1 - price_ratio)
                * 100
                * RankingWeights.PRICE
            )

        # ======================================
        # Prime
        # ======================================

        if product.get("prime"):

            score.prime_score = (
                100
                * RankingWeights.PRIME
            )

        # ======================================
        # Amazon Choice
        # ======================================

        if product.get("amazon_choice"):

            score.choice_score = (
                100
                * RankingWeights.AMAZON_CHOICE
            )

        # ======================================
        # Best Seller
        # ======================================

        if product.get("best_seller"):

            score.bestseller_score = (
                100
                * RankingWeights.BESTSELLER
            )

        # ======================================
        # Sponsored Penalty
        # ======================================

        if product.get("sponsored"):

            score.sponsored_penalty = (
                100
                * RankingWeights.SPONSORED
            )

        # ======================================
        # Final Score
        # ======================================

        score.final_score = (

            score.rating_score +

            score.review_score +

            score.price_score +

            score.prime_score +

            score.choice_score +

            score.bestseller_score -

            score.sponsored_penalty

        )

        return score