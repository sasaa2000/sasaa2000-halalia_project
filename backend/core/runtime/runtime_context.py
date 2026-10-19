from dataclasses import dataclass


@dataclass
class RuntimeContext:
    keyword: str
    provider_name: str
    started_at: float