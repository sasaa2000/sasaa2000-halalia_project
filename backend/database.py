import json
import os

ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_FILE = os.path.join(
    ROOT_DIR,
    "products_db.json"
)
def load_products():

    print("DB PATH =", DB_FILE)

    if not os.path.exists(DB_FILE):
        print("DATABASE NOT FOUND")
        return []

    try:

        with open(
            DB_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:
        return []


def save_product(product_data):

    products = load_products()

    product_name = (
        product_data.get("product_name", "")
        .strip()
        .lower()
    )

    # تجاهل الأوامر
    blocked = [
        "start/",
        "top/",
        "topsaved/",
        "/start",
        "/top",
        "/topsaved"
    ]

    if product_name in blocked:
        return

    for item in products:

        old_name = (
            item.get("product_name", "")
            .strip()
            .lower()
        )

        if old_name == product_name:

            if (
                product_data.get("score", 0)
                > item.get("score", 0)
            ):
                item.update(product_data)

            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    products,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            return

    products.append(product_data)

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(
            products,
            f,
            ensure_ascii=False,
            indent=4
        )