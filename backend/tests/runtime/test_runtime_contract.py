from backend.core.contracts.runtime_contract import RuntimeContract


def test_runtime_contract_version():
    assert RuntimeContract.VERSION == "1.0"

from backend.core.runtime.runtime_state import RuntimeState
from backend.core.runtime.runtime_engine import RuntimeEngine
from backend.core.runtime.runtime_context import RuntimeContext


def test_runtime_state_contract():
    assert RuntimeState.CREATED.value == "CREATED"
    assert RuntimeState.HEALTH_CHECK.value == "HEALTH_CHECK"
    assert RuntimeState.DOWNLOADING.value == "DOWNLOADING"
    assert RuntimeState.PARSING.value == "PARSING"
    assert RuntimeState.PIPELINE.value == "PIPELINE"
    assert RuntimeState.FINISHED.value == "FINISHED"
    assert RuntimeState.FAILED.value == "FAILED"

from backend.core.runtime.runtime_result import RuntimeResult


def test_runtime_result_contract():
    result = RuntimeResult(
        success=True,
        state=RuntimeState.FINISHED,
        products=[],
        execution_time=0.0,
        message="Runtime Finished",
    )

    assert result.success is True
    assert result.state == RuntimeState.FINISHED
    assert result.products == []
    assert result.execution_time == 0.0
    assert result.message == "Runtime Finished"

from backend.core.health.health_checker import HealthChecker


def test_health_checker_contract():
    checker = HealthChecker()

    checker.check(
        name="Provider",
        condition=True,
        success_message="Ready",
        failed_message="Missing Provider",
    )

    report = checker.run()

    assert report.is_healthy() is True
    assert report.summary()["healthy"] == 1
    assert report.summary()["failed"] == 0

def test_health_checker_failed_condition():
    checker = HealthChecker()

    checker.check(
        name="Provider",
        condition=False,
        success_message="Ready",
        failed_message="Missing Provider",
    )

    report = checker.run()

    assert report.is_healthy() is False
    assert report.summary()["healthy"] == 0
    assert report.summary()["failed"] == 1

class FakeProvider:

    def __init__(self):
        self.calls = []

    def build_url(self, keyword):
        self.calls.append(("build_url", keyword))
        return f"https://example.test/search?q={keyword}"

    def download_page(self, url):
        self.calls.append(("download_page", url))
        return "<html>fake</html>"

    def parse_products(self, html):
        self.calls.append(("parse_products", html))
        return ["product-1", "product-2"]

    def run_pipeline(self, products):
        self.calls.append(("run_pipeline", products))
        return products


def test_runtime_engine_success_flow():
    provider = FakeProvider()
    engine = RuntimeEngine(provider)

    result = engine.run("portable blender")

    assert result.success is True
    assert result.state == RuntimeState.FINISHED
    assert result.products == ["product-1", "product-2"]
    assert result.execution_time >= 0
    assert result.message == "Runtime Finished"

    assert provider.calls == [
        ("build_url", "portable blender"),
        (
            "download_page",
            "https://example.test/search?q=portable blender",
        ),
        ("parse_products", "<html>fake</html>"),
        ("run_pipeline", ["product-1", "product-2"]),
    ]


def test_runtime_engine_failure_flow():
    class FailingProvider:

        def build_url(self, keyword):
            raise RuntimeError("Provider failure")

    engine = RuntimeEngine(FailingProvider())

    result = engine.run("portable blender")

    assert result.success is False
    assert result.state == RuntimeState.FAILED
    assert result.products == []
    assert result.message == "Provider failure"
    assert result.execution_time >= 0


def test_runtime_engine_health_check_failure():
    engine = RuntimeEngine(None)

    result = engine.run("portable blender")

    assert result.success is False
    assert result.state == RuntimeState.FAILED
    assert result.products == []
    assert result.message == "Health Check Failed"
    assert result.execution_time >= 0


def test_runtime_engine_execution_order():
    calls = []

    class OrderedProvider:

        def build_url(self, keyword):
            calls.append("build_url")
            return "https://example.com/search"

        def download_page(self, url):
            calls.append("download_page")
            return "<html>products</html>"

        def parse_products(self, html):
            calls.append("parse_products")
            return ["product"]

        def run_pipeline(self, products):
            calls.append("run_pipeline")
            return products

    engine = RuntimeEngine(OrderedProvider())

    result = engine.run("portable blender")

    assert result.success is True
    assert result.state == RuntimeState.FINISHED

    assert calls == [
        "build_url",
        "download_page",
        "parse_products",
        "run_pipeline",
    ]


def test_runtime_engine_pipeline_failure_flow():
    class PipelineFailingProvider:

        def build_url(self, keyword):
            return "https://example.com/search"

        def download_page(self, url):
            return "<html>products</html>"

        def parse_products(self, html):
            return ["product"]

        def run_pipeline(self, products):
            raise RuntimeError("Pipeline failure")

    engine = RuntimeEngine(PipelineFailingProvider())

    result = engine.run("portable blender")

    assert result.success is False
    assert result.state == RuntimeState.FAILED
    assert result.products == []
    assert result.message == "Pipeline failure"
    assert result.execution_time >= 0


def test_runtime_engine_download_failure_flow():
    class DownloadFailingProvider:

        def build_url(self, keyword):
            return "https://example.com/search"

        def download_page(self, url):
            return ""

        def parse_products(self, html):
            raise AssertionError("Parser must not be called")

        def run_pipeline(self, products):
            raise AssertionError("Pipeline must not be called")

    engine = RuntimeEngine(DownloadFailingProvider())

    result = engine.run("portable blender")

    assert result.success is False
    assert result.state == RuntimeState.FAILED
    assert result.products == []
    assert result.message == "Download Failed"
    assert result.execution_time >= 0


def test_runtime_engine_parser_failure_flow():
    class ParserFailingProvider:

        def build_url(self, keyword):
            return "https://example.com/search"

        def download_page(self, url):
            return "<html>products</html>"

        def parse_products(self, html):
            raise RuntimeError("Parser failure")

        def run_pipeline(self, products):
            raise AssertionError("Pipeline must not be called")

    engine = RuntimeEngine(ParserFailingProvider())

    result = engine.run("portable blender")

    assert result.success is False
    assert result.state == RuntimeState.FAILED
    assert result.products == []
    assert result.message == "Parser failure"
    assert result.execution_time >= 0


def test_runtime_context_contract():
    context = RuntimeContext(
        keyword="portable blender",
        provider_name="AmazonProvider",
        started_at=123.45,
    )

    assert context.keyword == "portable blender"
    assert context.provider_name == "AmazonProvider"
    assert context.started_at == 123.45


def test_runtime_engine_creates_context():
    provider = FakeProvider()
    engine = RuntimeEngine(provider)

    result = engine.run("portable blender")

    assert result.success is True
    assert hasattr(engine, "context")
    assert engine.context.keyword == "portable blender"
    assert engine.context.provider_name == "FakeProvider"
    assert engine.context.started_at > 0


def test_runtime_engine_creates_context():
    provider = FakeProvider()
    engine = RuntimeEngine(provider)

    result = engine.run("portable blender")

    assert result.success is True
    assert hasattr(engine, "context")
    assert engine.context.keyword == "portable blender"
    assert engine.context.provider_name == "FakeProvider"
    assert engine.context.started_at > 0

