class ParserResult:

    def __init__(self):

        self.products = []

        self.errors = []

    def add_product(self, product):

        self.products.append(product)

    def add_error(self, error):

        self.errors.append(error)

    @property
    def success(self):

        return len(self.products) > 0