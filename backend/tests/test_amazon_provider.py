from pprint import pprint

from backend.providers.amazon_provider import AmazonProvider


def main():

    provider = AmazonProvider()

    print("=" * 60)
    print("Searching Amazon...")
    print("=" * 60)

    products = provider.search(
        keyword="portable blender",
        limit=5
    )

    print()

    print(f"Products Found : {len(products)}")

    print("=" * 60)

    for index, product in enumerate(products, start=1):

        print()

        print(f"Product #{index}")

        pprint(product)

        print("-" * 60)


if __name__ == "__main__":

    main()