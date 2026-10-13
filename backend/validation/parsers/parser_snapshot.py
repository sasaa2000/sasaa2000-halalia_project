from dataclasses import dataclass

from backend.core.models.product import Product


@dataclass
class ParserSnapshot:

    raw_html: str

    parsed_products: list[Product]