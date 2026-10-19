from dataclasses import dataclass
from typing import List

from backend.core.models.product import Product


@dataclass
class RuntimeResult:

    success: bool

    state: str

    products: List[Product]

    execution_time: float

    message: str