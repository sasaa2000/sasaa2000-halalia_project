from dataclasses import dataclass


@dataclass
class NetworkReport:

    status_code: int

    response_time: float

    html_size: int

    blocked: bool

    redirected: bool

    success: bool

    message: str