from backend.sources.amazon_source import get_products

from backend.hunter_pipeline import run_pipeline

import traceback

print("DISCOVERY_ENGINE LOADED")


def get_top_products():

    print("GET_TOP_PRODUCTS CALLED")

    products = get_products()

    results = []

    for product in products:

        try:

            print(f"PIPELINE: {product['name']}")

            results.append(
            run_pipeline(product)
            )

            print(f"DONE: {product['name']}")

        except Exception as error:

            print("\n========== PIPELINE ERROR ==========")
            print(f"Product : {product['name']}")
            print(f"Error   : {error}")
            traceback.print_exc()
            print("====================================\n")

            raise

    return results