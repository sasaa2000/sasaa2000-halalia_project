from dataclasses import dataclass
from typing import List

from .stage_result import StageResult


@dataclass
class PipelineReport:

    stages: List[StageResult]

    total_input: int

    total_output: int

    success: bool