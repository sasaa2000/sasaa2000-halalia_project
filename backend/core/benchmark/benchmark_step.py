from dataclasses import dataclass


@dataclass
class BenchmarkStep:

    name: str

    duration: float