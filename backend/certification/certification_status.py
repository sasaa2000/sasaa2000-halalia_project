from enum import Enum


class CertificationStatus(str, Enum):

    PASSED = "PASSED"

    FAILED = "FAILED"

    WARNING = "WARNING"