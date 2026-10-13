from dataclasses import dataclass


@dataclass
class FieldValidation:

    field: str

    extracted: bool

    value: str | None

    message: str