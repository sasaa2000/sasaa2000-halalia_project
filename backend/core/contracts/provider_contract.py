"""
Provider Contract
"""

from abc import ABC
from abc import abstractmethod


class ProviderContract(ABC):

    @abstractmethod
    def build_url(self, keyword):
        pass

    @abstractmethod
    def download_page(self, url):
        pass

    @abstractmethod
    def parse_products(self, html):
        pass

    @abstractmethod
    def run_pipeline(self, products):
        pass

    @abstractmethod
    def search(self, keyword, limit=20):
        pass