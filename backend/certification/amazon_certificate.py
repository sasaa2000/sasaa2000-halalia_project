from dataclasses import dataclass


@dataclass
class AmazonCertificate:

    provider: str

    framework_version: str

    runtime_version: str

    parser_version: str

    certified: bool