from dataclasses import dataclass


@dataclass
class ComponentCheck:

    name: str

    status: str

    message: str