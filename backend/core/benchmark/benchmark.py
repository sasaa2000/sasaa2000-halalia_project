from .timer import Timer
from .benchmark_step import BenchmarkStep
from .benchmark_report import BenchmarkReport


class Benchmark:

    def __init__(self):

        self.timer = Timer()

        self.report = BenchmarkReport()

    def begin(self):

        self.timer.start()

    def end(self, step_name):

        elapsed = self.timer.stop()

        self.report.add(

            BenchmarkStep(

                step_name,

                elapsed

            )

        )

        self.timer.start()