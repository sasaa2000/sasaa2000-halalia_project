from dataclasses import dataclass


@dataclass
class StabilityMetrics:

    success_rate: float

    average_time: float

    min_time: float

    max_time: float

    total_runs: int

    failed_runs: int