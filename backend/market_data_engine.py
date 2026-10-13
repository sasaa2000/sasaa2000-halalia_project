from backend.providers.amazon_provider import AmazonProvider
from backend.providers.mock_provider import MockProvider


amazon = AmazonProvider()

mock = MockProvider()


def get_market_data(product_name):

    data = amazon.search_product(product_name)

    if data is None:

        print("Amazon unavailable -> Mock Provider")

        data = mock.search_product(product_name)

    return data