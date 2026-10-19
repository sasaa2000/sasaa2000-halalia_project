from backend.providers.amazon_provider import AmazonProvider

from backend.core.runtime.runtime_engine import RuntimeEngine

from backend.core.logging import logger

provider = AmazonProvider()

engine = RuntimeEngine(provider)

result = engine.run(

    keyword="wireless earbuds"

)

if result.success:

    logger.info(

        "Runtime",

        "Execution Successful"

    )

else:

    logger.error(

        "Runtime",

        result.message

    )

