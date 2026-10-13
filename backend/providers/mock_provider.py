from backend.providers.market_provider import MarketProvider


class MockProvider(MarketProvider):

    def search_product(self, product_name):

        return {

            "search_results": 2350,

            "average_price": 41,

            "average_rating": 4.6,

            "average_reviews": 2800,

            "top_seller_reviews": 21000,

            "top_seller_rating": 4.8,

            "competition_index": 63,

            "market_depth": 72,

            "best_seller": True

        }