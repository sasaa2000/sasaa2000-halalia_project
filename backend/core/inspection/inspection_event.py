from dataclasses import dataclass
from datetime import datetime


@dataclass
class InspectionEvent:

    stage: str

    message: str

    success: bool = True

    timestamp: datetime = datetime.now()