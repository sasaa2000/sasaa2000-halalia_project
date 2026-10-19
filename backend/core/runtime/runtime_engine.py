import time

from backend.core.logging import logger
from backend.core.health.health_checker import HealthChecker

from .runtime_context import RuntimeContext
from .runtime_result import RuntimeResult
from .runtime_state import RuntimeState


class RuntimeEngine:

    def __init__(self, provider):
        self.provider = provider

    def run(self, keyword):
        start = time.time()

        self.context = RuntimeContext(
            keyword=keyword,
            provider_name=(
                type(self.provider).__name__
                if self.provider is not None
                else "None"
            ),
            started_at=start,
        )

        runtime_logger = logger.get_logger("HALALIA_RUNTIME")
        runtime_logger.info("Runtime Started")

        checker = HealthChecker()

        checker.check(
            name="Provider",
            condition=self.provider is not None,
            success_message="Ready",
            failed_message="Missing Provider",
        )

        report = checker.run()

        if not report.is_healthy():
            execution = time.time() - start

            runtime_logger.error("Health Check Failed")

            return RuntimeResult(
                success=False,
                state=RuntimeState.FAILED,
                products=[],
                execution_time=execution,
                message="Health Check Failed",
            )

        try:
            url = self.provider.build_url(keyword)

            html = self.provider.download_page(url)

            if not html:
                execution = time.time() - start

                runtime_logger.error("Download Failed")

                return RuntimeResult(
                    success=False,
                    state=RuntimeState.FAILED,
                    products=[],
                    execution_time=execution,
                    message="Download Failed",
                )

            products = self.provider.parse_products(html)

            products = self.provider.run_pipeline(products)

            execution = time.time() - start

            runtime_logger.info(
                f"Finished in {execution:.2f}s"
            )

            return RuntimeResult(
                success=True,
                state=RuntimeState.FINISHED,
                products=products,
                execution_time=execution,
                message="Runtime Finished",
            )

        except Exception as exc:
            execution = time.time() - start

            runtime_logger.error(
                f"Runtime Failed: {exc}"
            )

            return RuntimeResult(
                success=False,
                state=RuntimeState.FAILED,
                products=[],
                execution_time=execution,
                message=str(exc),
            )
