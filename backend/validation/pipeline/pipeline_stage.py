from enum import Enum


class PipelineStage(str, Enum):

    VALIDATION = "Validation"

    NORMALIZATION = "Normalization"

    PRICE_ENGINE = "Price Engine"

    RANKING = "Ranking"