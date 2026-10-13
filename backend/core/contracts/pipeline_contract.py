"""
Pipeline Contract
"""

from abc import ABC
from abc import abstractmethod


class PipelineContract(ABC):

    @abstractmethod
    def run(self, products):
        """
        Receive List[Product]

        Return List[Product]
        """
        pass