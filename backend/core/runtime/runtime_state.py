from enum import Enum


class RuntimeState(str, Enum):

    CREATED = "CREATED"

    HEALTH_CHECK = "HEALTH_CHECK"

    DOWNLOADING = "DOWNLOADING"

    PARSING = "PARSING"

    PIPELINE = "PIPELINE"

    FINISHED = "FINISHED"

    FAILED = "FAILED"