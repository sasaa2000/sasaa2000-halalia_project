"""
Parser Contract
"""

from abc import ABC
from abc import abstractmethod


class ParserContract(ABC):

    @abstractmethod
    def parse(self, html):
        """
        Receive HTML

        Return List[Product]
        """
        pass