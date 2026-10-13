from dataclasses import dataclass

from .stability_metrics import StabilityMetrics

from .stress_iteration import StressIteration


@dataclass
class StressReport:

    iterations: list[StressIteration]

    metrics: StabilityMetrics

    success: bool