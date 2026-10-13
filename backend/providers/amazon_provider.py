import urllib.parse
from pathlib import Path

from backend.network.engines.request_engine import RequestEngine

from backend.parsers.amazon_parser import AmazonParser

from backend.core.pipeline.product_pipeline import ProductPipeline


class AmazonProvider:
    """
    HALALIA Amazon Provider

    Responsibilities

        Build Search URL

        Download HTML

        Parse HTML

        Run HALALIA Pipeline

        Return Products
    """

    BASE_URL = "https://www.amazon.com/s"

    # ==================================================
    # Constructor
    # ==================================================

    def __init__(self):

        self.request_engine = RequestEngine()

        self.parser = AmazonParser()

        self.pipeline = ProductPipeline()

    # ==================================================
    # Public API
    # ==================================================

    def search(

        self,

        keyword: str,

        limit: int = 20

    ):

        url = self.build_url(keyword)

        html = self.download_page(url)

        if not html:

            return []

        products = self.parse_products(html)

        products = self.run_pipeline(products)

        return products[:limit]

    # ==================================================
    # URL Builder
    # ==================================================

    def build_url(

        self,

        keyword: str

    ) -> str:

        keyword = urllib.parse.quote(keyword)

        return f"{self.BASE_URL}?k={keyword}"

    # ==================================================
    # Downloader
    # ==================================================

    def download_page(

        self,

        url: str

    ) -> str:

        response = self.request_engine.get(url)

        if response is None:

            return ""

        if not hasattr(response, "text"):

            return ""

        html = response.text

        self.save_debug_page(html)

        return html

    # ==================================================
    # Save HTML
    # ==================================================

    def save_debug_page(

        self,

        html: str

    ):

        try:

            debug_dir = Path("backend/debug")

            debug_dir.mkdir(

                parents=True,

                exist_ok=True

            )

            file = debug_dir / "amazon_page.html"

            file.write_text(

                html,

                encoding="utf-8"

            )

        except Exception as e:

            print(

                "Debug Save Error:",

                e

            )

    # ==================================================
    # Parser
    # ==================================================

    def parse_products(

        self,

        html: str

    ):

        if not html:

            return []

        try:

            return self.parser.parse(html)

        except Exception as e:

            print(

                "Parser Error:",

                e

            )

            return []

    # ==================================================
    # HALALIA Pipeline
    # ==================================================

    def run_pipeline(

        self,

        products

    ):

        if not products:

            return []

        try:

            return self.pipeline.run(products)

        except Exception as e:

            print(

                "Pipeline Error:",

                e

            )

            return products

