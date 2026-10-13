from backend.parsers.amazon_parser import AmazonParser

from .field_validation import FieldValidation

from .parser_report import ParserReport

from .parser_snapshot import ParserSnapshot

class AmazonParserValidator:

    def __init__(self):

        self.parser = AmazonParser()

        def validate(

                self,

                html

        ):
            products = self.parser.parse(html)

            fields = []

            for product in products:
                fields.append(

                    FieldValidation(

                        field="name",

                        extracted=bool(product.name),

                        value=product.name,

                        message="OK"

                        if product.name

                        else "Missing Name"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="price",

                        extracted=product.price is not None,

                        value=str(product.price),

                        message="OK"

                        if product.price

                        else "Price Missing"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="asin",

                        extracted=bool(product.asin),

                        value=product.asin,

                        message="OK"

                        if product.asin

                        else "ASIN Missing"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="url",

                        extracted=bool(product.url),

                        value=product.url,

                        message="OK"

                        if product.url

                        else "URL Missing"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="rating",

                        extracted=product.rating is not None,

                        value=str(product.rating),

                        message="OK"

                        if product.rating

                        else "Rating Missing"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="reviews",

                        extracted=product.review_count is not None,

                        value=str(product.review_count),

                        message="OK"

                        if product.review_count

                        else "Review Count Missing"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="prime",

                        extracted=True,

                        value=str(product.is_prime),

                        message="Detected"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="sponsored",

                        extracted=True,

                        value=str(product.is_sponsored),

                        message="Detected"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="amazon_choice",

                        extracted=True,

                        value=str(product.is_amazon_choice),

                        message="Detected"

                    )

                )

                fields.append(

                    FieldValidation(

                        field="best_seller",

                        extracted=True,

                        value=str(product.is_best_seller),

                        message="Detected"

                    )

                )

                snapshot = ParserSnapshot(

                    raw_html=html,

                    parsed_products=products

                )

                report = ParserReport(

                    total_products=len(products),

                    valid_products=len(

                        [

                            p

                            for p in products

                            if p.name and p.price

                        ]

                    ),

                    failed_products=len(

                        [

                            p

                            for p in products

                            if not p.name or p.price is None

                        ]

                    ),

                    fields=fields

                )

                return (

                    report,

                    snapshot

                )

