from backend.core.runtime.runtime_engine import RuntimeEngine

from .benchmark_history import BenchmarkHistory

from .stress_iteration import StressIteration

from .stress_report import StressReport

from .stability_metrics import StabilityMetrics


class RuntimeStressTest:

    def __init__(self, provider):

        self.engine = RuntimeEngine(provider)

        def run(

                self,

                keywords: list[str]

        ):
            iterations = []

            history = BenchmarkHistory()

            for index, keyword in enumerate(keywords):

                try:
                    result = self.engine.run(keyword)

                    history.add(
                        result.execution_time
                    )

                    iterations.append(
                        StressIteration(
                            iteration=index + 1,
                            keyword=keyword,
                            success=result.success,
                            execution_time=result.execution_time,
                            products_found=len(result.products),
                        )
                    )

                except Exception as exc:
                    iterations.append(
                        StressIteration(
                            iteration=index + 1,
                            keyword=keyword,
                            success=False,
                            execution_time=0,
                            products_found=0,
                            error=str(exc),
                        )
                    )

                iterations.append(

                    StressIteration(

                        iteration=index + 1,

                        keyword=keyword,

                        success=False,

                        execution_time=0,

                        products_found=0,

                        error=str(exc)

                    )

                )

                successful = [

                    item

                    for item in iterations

                    if item.success

                ]

                metrics = StabilityMetrics(

                    success_rate=(

                                         len(successful)

                                         /

                                         len(iterations)

                                 ) * 100,

                    average_time=history.average,

                    min_time=history.minimum,

                    max_time=history.maximum,

                    total_runs=len(iterations),

                    failed_runs=len(iterations) - len(successful)

                )

                report = StressReport(

                    iterations=iterations,

                    metrics=metrics,

                    success=(

                            metrics.success_rate >= 95

                    )

                )

                return report

            keywords = [

                "wireless earbuds",

                "iphone charger",

                "bluetooth speaker",

                "portable blender",

                "gaming mouse",

                "laptop stand",

                "usb c hub",

                "office chair",

                "mechanical keyboard",

                "smart watch"

            ]

            report = stress_test.run(

                keywords

            )





