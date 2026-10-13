from backend.core.validation.product_validator import ProductValidator

from backend.core.normalization.product_normalizer import ProductNormalizer

from backend.core.pricing.price_engine import PriceEngine

from backend.core.ranking.product_ranker import ProductRanker


class ProductPipeline:

    """
    HALALIA Product Pipeline

    Parser
        ↓
    Validation
        ↓
    Normalization
        ↓
    Pricing
        ↓
    Ranking
    """

    @classmethod
    def run(cls, products):

        valid_products = []

        for product in products:

            validation = ProductValidator.validate(product)

            if not validation["valid"]:
                continue

            product = ProductNormalizer.normalize(product)

            product = PriceEngine.process(product)

            valid_products.append(product)

        ranked_products = ProductRanker.rank(valid_products)

        return ranked_products