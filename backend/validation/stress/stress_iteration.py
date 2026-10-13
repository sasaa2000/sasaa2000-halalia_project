from dataclasses import dataclass


@dataclass
class StressIteration:

    iteration: int

    keyword: str

    success: bool

    execution_time: float

    products_found: int

    error: str | None = None