from bs4 import BeautifulSoup

from backend.parsers.product_factory import ProductFactory


class BaseParser:

    def __init__(self):

        self.soup = None

    def parse(self, html):

        self.soup = BeautifulSoup(html, "lxml")

        return self.parse_products()

    def product(self):

        return ProductFactory.create()

    def parse_products(self):

        raise NotImplementedError