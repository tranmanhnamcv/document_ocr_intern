from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ─── OCR page schemas ─────────────────────────────────────────────────────────
class OCRPageResponse(BaseModel):
    id: int
    page_number: int
    extracted_text: str|None = None
    confidence: float|None = None
    pipeline_used: str|None = None
    quality_report: dict|None = None

    class Config:
        from_attributes = True


# ─── Document schemas ─────────────────────────────────────────────────────────
class DocumentBase(BaseModel):
    original_filename: str
    file_type: str|None = None
    mime_type: str|None = None


class DocumentCreate(DocumentBase):
    filename: str
    file_path: str
    file_size: int|None = None


class DocumentResponse(DocumentBase):
    id: int
    filename: str
    user_id: int|None = None
    file_size: int|None = None
    status: str
    extracted_text: str|None = None
    total_pages: int|None = None
    average_confidence: float|None = None
    error_message: str|None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Extended response that includes per-page OCR results."""
    pages: List[OCRPageResponse] = []

    class Config:
        from_attributes = True


# ─── Upload response ──────────────────────────────────────────────────────────
class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse

# ── Search ────────────────────────────────────────────────────────────────────

class SearchResultItem(BaseModel):
    document: DocumentResponse
    rank: float
    headline: str|None = None   # HTML snippet with <mark> highlights


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]
    page: int
    limit: int