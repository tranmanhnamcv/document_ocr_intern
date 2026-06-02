from dataclasses import dataclass
from typing import Optional

@dataclass
class PageResult:
    page_number: int
    text: str
    confidence: float
    quality_report: dict|None = None