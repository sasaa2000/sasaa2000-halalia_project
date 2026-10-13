from bs4 import BeautifulSoup

from backend.core.models.product import Product


class BaseParser:

    SOURCE = ""

    def __init__(self):

        self.html = ""

        self.soup = None

    # =======================================================
    # Parse HTML
    # =======================================================

    def parse(self, html):

        self.html = html

        self.soup = BeautifulSoup(
            html,
            "lxml"
        )

        return self.parse_products()

    # =======================================================
    # Create Product
    # =======================================================

    def product(self):

        product = Product()

        product.source = self.SOURCE

        product.marketplace = self.SOURCE

        return product

    # =======================================================
    # Parse Products
    # =======================================================

    def parse_products(self):

        raise NotImplementedError