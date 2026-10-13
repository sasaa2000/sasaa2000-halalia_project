from backend.providers.provider import Provider


class CJDropshippingProvider(Provider):

    name = "cjdropshipping"

    def search_products(
        self,
        keyword,
        limit=20
    ):

        print(f"[CJ] Searching: {keyword}")

        return []