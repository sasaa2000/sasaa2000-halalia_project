from dataclasses import dataclass
from typing import List

from .field_validation import FieldValidation


@dataclass
class ParserReport:

    total_products: int

    valid_products: int

    failed_products: int

    fields: List[FieldValidation]