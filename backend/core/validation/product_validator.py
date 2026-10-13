from backend.core.models.product import Product


class ProductValidator:

    # ==========================================
    # Main Validation
    # ==========================================

    @classmethod
    def validate(cls, product: Product):

        errors = []

        if not cls.has_name(product):
            errors.append("Missing Product Name")

        if not cls.has_url(product):
            errors.append("Missing Product URL")

        if not cls.has_image(product):
            errors.append("Missing Product Image")

        if not cls.has_price(product):
            errors.append("Missing Product Price")

        return {

            "valid": len(errors) == 0,

            "errors": errors

        }

    # ==========================================
    # Individual Rules
    # ==========================================

    @staticmethod
    def has_name(product):

        return bool(product.product_name.strip())

    @staticmethod
    def has_url(product):

        return bool(product.url.strip())

    @staticmethod
    def has_image(product):

        return bool(product.image.strip())

    @staticmethod
    def has_price(product):

        return product.price is not None

    @staticmethod
    def has_rating(product):

        return product.rating >= 0

    @staticmethod
    def has_reviews(product):

        return product.reviews >= 0

    @staticmethod
    def has_currency(product):

        return bool(product.currency)