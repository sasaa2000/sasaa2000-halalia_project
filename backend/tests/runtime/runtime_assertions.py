class RuntimeAssertions:

    @staticmethod
    def assert_html(html):

        return bool(html)


    @staticmethod
    def assert_products(products):

        return isinstance(products, list)


    @staticmethod
    def assert_pipeline(products):

        return len(products) > 0


    @staticmethod
    def assert_scores(products):

        for product in products:

            if getattr(product, "score", None) is None:

                return False

        return True