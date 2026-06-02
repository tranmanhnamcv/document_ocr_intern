from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from models.ocr_result import OCRResult
from schemas.ocr_result import PageResult

class OCRResultRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Write ──────────────────────────────────────────────────────────────────

    def create_bulk(
        self, document_id: int, pages: List[PageResult]
    ) -> List[OCRResult]:
        """
        Persist a list of PageResult objects as rows in ocr_results.
        All rows are flushed in a single commit.
        """
        rows: List[OCRResult] = []
        for page in pages:
            pipeline = (
                page.quality_report.get("pipeline")
                if page.quality_report
                else None
            )
            row = OCRResult(
                document_id=document_id,
                page_number=page.page_number,
                extracted_text=page.text,
                confidence=page.confidence,
                quality_report=page.quality_report,
                pipeline_used=pipeline,
            )
            self.db.add(row)
            rows.append(row)

        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_by_document_id(self, document_id: int) -> List[OCRResult]:
        return (
            self.db.query(OCRResult)
            .filter(OCRResult.document_id == document_id)
            .order_by(OCRResult.page_number)
            .all()
        )

    def get_by_id(self, result_id: int) -> OCRResult|None:
        return (
            self.db.query(OCRResult)
            .filter(OCRResult.id == result_id)
            .first()
        )

    # ── Delete ─────────────────────────────────────────────────────────────────

    def delete_by_document_id(self, document_id: int) -> int:
        """Remove all OCR rows for a document. Returns the number of deleted rows."""
        deleted = (
            self.db.query(OCRResult)
            .filter(OCRResult.document_id == document_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted