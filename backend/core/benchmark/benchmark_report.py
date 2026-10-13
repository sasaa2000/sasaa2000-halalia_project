class BenchmarkReport:

    def __init__(self):

        self.steps = []

    def add(self, step):

        self.steps.append(step)

    @property
    def total_time(self):

        return sum(

            item.duration

            for item in self.steps

        )

    def print(self):

        print()

        print("=" * 60)

        print("HALALIA PERFORMANCE REPORT")

        print("=" * 60)

        for step in self.steps:

            print(

                f"{step.name:25}"

                f"{step.duration:.4f} sec"

            )

        print("-" * 60)

        print(

            f"{'TOTAL':25}"

            f"{self.total_time:.4f} sec"

        )

        print("=" * 60)