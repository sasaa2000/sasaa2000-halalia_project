from backend.core.models.product import Product

from backend.core.helpers.parser_helpers import clean_text


class ProductNormalizer:

    # ==========================================
    # Main Entry
    # ==========================================

    @classmethod
    def normalize(cls, product: Product):

        cls.normalize_name(product)

        cls.normalize_price(product)

        cls.normalize_rating(product)

        cls.normalize_reviews(product)

        cls.normalize_url(product)

        cls.normalize_image(product)

        cls.normalize_currency(product)

        return product

    # ==========================================
    # Name
    # ==========================================

    @staticmethod
    def normalize_name(product):

        product.product_name = clean_text(
            product.product_name
        )

    # ==========================================
    # Price
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
    # Rating
    # ==========================================

    @staticmethod
    def normalize_rating(product):

        if product.rating is None:
            product.rating = 0.0

        if product.rating < 0:
            product.rating = 0.0

        if product.rating > 5:
            product.rating = 5.0

    # ==========================================
    # Reviews
    # ==========================================

    @staticmethod
    def normalize_reviews(product):

        if product.reviews is None:
            product.reviews = 0

        if product.reviews < 0:
            product.reviews = 0

    # ==========================================
    # URL
    # ==========================================

    @staticmethod
    def normalize_url(product):

        if product.url:

            product.url = product.url.strip()

    # ==========================================
    # Image
    # ==========================================

    @staticmethod
    def normalize_image(product):

        if product.image:

            product.image = product.image.strip()

    # ==========================================
    # Currency
    # ==========================================

    @staticmethod
    def normalize_currency(product):

        if not product.currency:

            product.currency = "USD"

        product.currency = product.currency.upper()