from backend.core.models.product import Product


class ProductNormalizer:

    @classmethod
    def normalize(

        cls,

        product: Product

    ):

        if product.product_name:

            product.product_name = (

                product.product_name.strip()

            )

        if product.currency:

            product.currency = (

                product.currency.upper()

            )

        return product