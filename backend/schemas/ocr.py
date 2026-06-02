"""
Pydantic schemas for the OCR API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class PageResultSchema(BaseModel):
    page_number: int
    text: str
    confidence: float = Field(..., ge=0, le=100)
    word_count: int

    model_config = {"from_attributes": True}


class OCRResponseSchema(BaseModel):
    filename: str
    file_type: str
    total_pages: int
    full_text: str
    pages: list[PageResultSchema]
    avg_confidence: float = Field(..., ge=0, le=100)
    processing_time_ms: float
    succeeded: bool

    model_config = {"from_attributes": True}


class OCRErrorSchema(BaseModel):
    filename: str
    error: str