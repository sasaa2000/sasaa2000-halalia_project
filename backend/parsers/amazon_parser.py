from backend.parsers.base_parser import BaseParser
from backend.parsers.helpers import (
    attr,
    extract_price,
    extract_rating,
    extract_reviews,
    has_text,
    normalize_image,
    normalize_url,
    text,
)


class AmazonParser(BaseParser):

    SOURCE = "amazon"

    def parse_products(self):
        products = []

        cards = self.soup.select(
            "[data-component-type='s-search-result']"
        )

        for card in cards:
            try:
                product = self.product()

                product.asin = card.get(
                    "data-asin",
                    ""
                ).strip()

                title = card.select_one("h2 span")
                product.product_name = text(title)

                whole = text(
                    card.select_one("span.a-price-whole")
                )

                fraction = text(
                    card.select_one("span.a-price-fraction")
                )

                if whole:
                    price = whole

                    if fraction:
                        price += "." + fraction

                    product.price = extract_price(price)

                rating = text(
                    card.select_one("span.a-icon-alt")
                )

                product.rating = extract_rating(rating)

                reviews = text(
                    card.select_one(
                        "span.a-size-base.s-underline-text"
                    )
                )

                product.reviews = extract_reviews(reviews)

                image = card.select_one("img")

                product.image = normalize_image(
                    attr(image, "src")
                )

                link = card.select_one("h2 a")

                product.url = normalize_url(
                    attr(link, "href")
                )

                product.is_sponsored = has_text(
                    card,
                    "Sponsored"
                )

                product.is_prime = (
                    card.select_one(".a-icon-prime") is not None
                )

                product.amazon_choice = has_text(
                    card,
                    "Amazon's Choice"
                )

                product.best_seller = has_text(
                    card,
                    "Best Seller"
                )

                product.currency = "USD"

                if product.product_name:
                    products.append(
                        product.to_dict()
                    )

            except Exception:
                continue

        return products
