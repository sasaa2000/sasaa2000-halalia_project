from dataclasses import dataclass
from typing import List

from .certification_rules import CertificationRule


@dataclass
class CertificationReport:

    provider: str

    version: str

    rules: List[CertificationRule]

    passed: bool