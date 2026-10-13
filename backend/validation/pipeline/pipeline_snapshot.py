from dataclasses import dataclass

from backend.core.models.product import Product


@dataclass
class PipelineSnapshot:

    before_pipeline: list[Product]

    after_pipeline: list[Product]