from backend.core.models.product import Product


class PriceEngine:

    # ==========================================
    # Main Entry
    # ==========================================

    @classmethod
    def process(cls, product: Product):

        cls.calculate_discount(product)

        cls.normalize_price(product)

        return product

    # ==========================================
    # Normalize Price
    # ==========================================

    @staticmethod
    def normalize_price(product):

        if product.price is None:
            return

        product.price = round(
            float(product.price),
            2
        )

    # ==========================================
    # Discount Calculation
    # ==========================================

    @staticmethod
    def calculate_discount(product):

        if product.price is None:
            return

        if product.original_price is None:
            return

        if product.original_price <= product.price:
            product.discount = 0
            return

        difference = (
            product.original_price
            - product.price
        )

        percent = (
            difference
            / product.original_price
        ) * 100

        product.discount = round(
            percent,
            2
        )

    # ==========================================
    # Has Discount
    # ==========================================

    @staticmethod
    def has_discount(product):

        return (
            product.discount is not None
            and
            product.discount > 0
        )

    # ==========================================
    # Final Price
    # ==========================================

    @staticmethod
    def final_price(product):

        return product.price