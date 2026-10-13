from dataclasses import dataclass


@dataclass
class CertificationRule:

    name: str

    passed: bool

    message: str