from dataclasses import dataclass


@dataclass
class ResponseSnapshot:

    url: str

    html: str

    response_headers: dict