from backend.core.models.product import Product

from backend.core.ranking.ranking_rules import RankingRules


class ProductRanker:

    # ==========================================
    # Rank Products
    # ==========================================

    @classmethod
    def rank(cls, products):

        for product in products:

            cls.calculate(product)

        return sorted(

            products,

            key=lambda x: x.score,

            reverse=True

        )

    # ==========================================
    # Calculate Score
    # ==========================================

    @classmethod
    def calculate(cls, product: Product):

        score = 0

        score += RankingRules.rating(product)

        score += RankingRules.reviews(product)

        score += RankingRules.prime(product)

        score += RankingRules.amazon_choice(product)

        score += RankingRules.best_seller(product)

        score += RankingRules.discount(product)

        score += RankingRules.sponsored(product)

        product.score = round(score, 2)

        return product.score