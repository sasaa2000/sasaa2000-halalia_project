from backend.providers.amazon_provider import AmazonProvider


class ProviderManager:

    def __init__(self):

        self.providers = [

            AmazonProvider(),

            AliExpressProvider(),

        ]

    def search_product(self, product_name):

        for provider in self.providers:

            try:

                result = provider.search_product(product_name)

                if result:

                    return result

            except Exception as e:

                print(provider.__class__.__name__, e)

        return None