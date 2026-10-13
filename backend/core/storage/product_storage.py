from backend.core.models.product import Product


class ProductStorage:

    """
    Temporary Storage Layer

    المرحلة الحالية:
        تخزين داخل الذاكرة فقط

    المرحلة القادمة:
        SQLite

    ثم:

        PostgreSQL

        Redis

        MongoDB
    """

    def __init__(self):

        self.products = []

    # ==========================================
    # Add Product
    # ==========================================

    def add(self, product: Product):

        self.products.append(product)

    # ==========================================
    # Add List
    # ==========================================

    def extend(self, products):

        self.products.extend(products)

    # ==========================================
    # Get All
    # ==========================================

    def all(self):

        return self.products

    # ==========================================
    # Count
    # ==========================================

    def count(self):

        return len(self.products)

    # ==========================================
    # Clear
    # ==========================================

    def clear(self):

        self.products.clear()