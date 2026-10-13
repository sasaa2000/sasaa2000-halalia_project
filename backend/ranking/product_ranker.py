from backend.ranking.ranking_engine import RankingEngine
from backend.ranking.ranking_rules import RankingRules


class ProductRanker:

    """
    Main Ranking Interface

    All Providers should call this class.

    Amazon
    AliExpress
    Temu
    Ebay
    Etsy
    Shopify
    Walmart

    ↓

    ProductRanker.rank(products)
    """

    @classmethod
    def rank(cls, products):

        if not products:
            return []

        # =====================================
        # Remove Invalid Products
        # =====================================

        valid_products = cls.filter_products(products)

        if not valid_products:
            return []

        # =====================================
        # Ranking
        # =====================================

        ranked_products = RankingEngine.rank(
            valid_products
        )

        return ranked_products

    # =========================================
    # Product Filters
    # =========================================

    @classmethod
    def filter_products(cls, products):

        filtered = []

        for product in products:

            # -------------------------------
            # Name Required
            # -------------------------------

            if not product.get("product_name"):
                continue

            # -------------------------------
            # URL Required
            # -------------------------------

            if not product.get("url"):
                continue

            # -------------------------------
            # Image Required
            # -------------------------------

            if (
                RankingRules.REQUIRE_IMAGE
                and
                not product.get("image")
            ):
                continue

            # -------------------------------
            # Price Required
            # -------------------------------

            if (
                RankingRules.REQUIRE_PRICE
                and
                not product.get("price")
            ):
                continue

            # -------------------------------
            # Rating Filter
            # -------------------------------

            rating = float(
                product.get("rating", 0)
            )

            if rating < RankingRules.MIN_RATING:
                continue

            # -------------------------------
            # Review Filter
            # -------------------------------

            reviews = int(
                product.get("reviews", 0)
            )

            if reviews < RankingRules.MIN_REVIEWS:
                continue

            # -------------------------------
            # Price Filter
            # -------------------------------

            price = float(
                product.get("price", 0)
            )

            if (
                RankingRules.MAX_PRICE > 0
                and
                price > RankingRules.MAX_PRICE
            ):
                continue

            # -------------------------------
            # Sponsored
            # -------------------------------

            if (
                RankingRules.REMOVE_SPONSORED
                and
                product.get("sponsored")
            ):
                continue

            filtered.append(product)

        return filtered