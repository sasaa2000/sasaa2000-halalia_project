from backend.product_categories import CATEGORY_KEYWORDS


def detect_category(product_name):

    name = product_name.lower()

    for category, words in CATEGORY_KEYWORDS.items():

        for word in words:

            if word in name:
                return category

    return "general"
