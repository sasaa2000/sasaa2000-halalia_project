from dataclasses import dataclass


@dataclass
class StageResult:

    stage: str

    input_count: int

    output_count: int

    success: bool

    message: str