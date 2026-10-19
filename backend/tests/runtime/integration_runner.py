from backend.providers.amazon_provider import AmazonProvider

from .runtime_report import RuntimeReport
from .runtime_assertions import RuntimeAssertions
from backend.core.logging import logger

class IntegrationRunner:

    def __init__(self):

        self.provider = AmazonProvider()

        self.report = RuntimeReport()

        def run(

                self,

                keyword="portable blender"

        ):
            logger.info(

                "Runtime",

                "Integration Test Started"

            )

            url = self.provider.build_url(keyword)

            self.report.add(

                "Build URL",

                url is not None

            )

            html = self.provider.download_page(url)

            self.report.add(

                "Download HTML",

                RuntimeAssertions.assert_html(html)

            )

            products = self.provider.parse_products(html)

            self.report.add(

                "Parser",

                RuntimeAssertions.assert_products(products)

            )

            products = self.provider.run_pipeline(products)

            self.report.add(

                "Pipeline",

                RuntimeAssertions.assert_pipeline(products)

            )

            self.report.add(

                "Ranking",

                RuntimeAssertions.assert_scores(products)

            )

            logger.info(

                "Runtime",

                "Integration Finished"

            )

            self.report.print()

            return products

