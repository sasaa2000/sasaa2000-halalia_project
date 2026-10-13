from backend.cache_engine import get_cache
from backend.cache_engine import save_cache
from backend.providers.provider_manager import ProviderManager

from backend.hunter_pipeline import run_pipeline


class DataOrchestrator:

    def __init__(self):

        self.provider = ProviderManager()

    def analyze_product(self, product_name):

        # ===========================
        # Cache
        # ===========================

        cached = get_cache(product_name)

        if cached is not None:

            print("CACHE HIT:", product_name)

            return cached

        print("CACHE MISS:", product_name)

        # ===========================
        # Amazon
        # ===========================

        product = self.provider.search_product(
            product_name
        )

        # ===========================
        # Hunter AI
        # ===========================

        result = run_pipeline(product)

        # ===========================
        # Save Cache
        # ===========================

        save_cache(
            product_name,
            result
        )

        return result