from backend.pipeline.product_pipeline import ProductPipeline


from .pipeline_report import PipelineReport

from .pipeline_snapshot import PipelineSnapshot

from .stage_result import StageResult

from .pipeline_stage import PipelineStage

class PipelineValidator:

    def __init__(self):

        self.pipeline = ProductPipeline()

        def validate(

                self,

                products

        ):

            before = list(products)

            validated = self.pipeline.validator.run(products)

            validation_result = StageResult(

                stage=PipelineStage.VALIDATION,

                input_count=len(products),

                output_count=len(validated),

                success=True,

                message="Validation Completed"

            )

            normalized = self.pipeline.normalizer.run(validated)

            normalization_result = StageResult(

                stage=PipelineStage.NORMALIZATION,

                input_count=len(validated),

                output_count=len(normalized),

                success=True,

                message="Normalization Completed"

            )

            priced = self.pipeline.price_engine.run(normalized)

            price_result = StageResult(

                stage=PipelineStage.PRICE_ENGINE,

                input_count=len(normalized),

                output_count=len(priced),

                success=True,

                message="Price Engine Completed"

            )

            ranked = self.pipeline.ranker.run(priced)

            ranking_result = StageResult(

                stage=PipelineStage.RANKING,

                input_count=len(priced),

                output_count=len(ranked),

                success=True,

                message="Ranking Completed"

            )

            snapshot = PipelineSnapshot(

                before_pipeline=before,

                after_pipeline=ranked
            )

            report = PipelineReport(

                stages=[

                    validation_result,

                    normalization_result,

                    price_result,

                    ranking_result

                ],

                total_input=len(before),

                total_output=len(ranked),

                success=True

            )

            return (

                report,

                snapshot

            )

