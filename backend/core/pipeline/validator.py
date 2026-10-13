from backend.core.models.product import Product


class ProductValidator:

    REQUIRED_FIELDS = (

        "product_name",

        "url"

    )

    @classmethod
    def validate(cls, product: Product):

        if product is None:

            return False

        if not product.product_name:

            return False

        if not product.url:

            return False

        return True