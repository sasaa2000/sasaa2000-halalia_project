from backend.core.models.product import Product


class RankingRules:

    # ==========================================
    # Rating Score
    # ==========================================

    @staticmethod
    def rating(product: Product):

        return product.rating * 20

    # ==========================================
    # Reviews Score
    # ==========================================

    @staticmethod
    def reviews(product: Product):

        if product.reviews >= 5000:
            return 20

        if product.reviews >= 1000:
            return 16

        if product.reviews >= 500:
            return 12

        if product.reviews >= 100:
            return 8

        if product.reviews >= 10:
            return 4

        return 0

    # ==========================================
    # Prime Bonus
    # ==========================================

    @staticmethod
    def prime(product: Product):

        return 5 if product.is_prime else 0

    # ==========================================
    # Amazon Choice Bonus
    # ==========================================

    @staticmethod
    def amazon_choice(product: Product):

        return 8 if product.amazon_choice else 0

    # ==========================================
    # Best Seller Bonus
    # ==========================================

    @staticmethod
    def best_seller(product: Product):

        return 10 if product.best_seller else 0

    # ==========================================
    # Sponsored Penalty
    # ==========================================

    @staticmethod
    def sponsored(product: Product):

        return -5 if product.is_sponsored else 0

    # ==========================================
    # Discount Bonus
    # ==========================================

    @staticmethod
    def discount(product: Product):

        if product.discount is None:
            return 0

        return min(product.discount, 15)