from urllib.parse import urlparse


class ProductValidator:

    @staticmethod
    def valid_name(name):

        return bool(name and len(name.strip()) > 2)

    @staticmethod
    def valid_price(price):

        if price is None:
            return False

        try:
            return float(price) > 0
        except:
            return False

    @staticmethod
    def valid_url(url):

        if not url:
            return False

        try:

            result = urlparse(url)

            return bool(result.scheme and result.netloc)

        except:

            return False

    @staticmethod
    def validate(product):

        return ProductValidator.valid_name(product.product_name)