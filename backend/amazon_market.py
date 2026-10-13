from backend.providers.mock_provider import MockProvider


provider = MockProvider()


def get_amazon_market_data(product_name):

    return provider.search_product(product_name)