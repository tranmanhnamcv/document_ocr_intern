from __future__ import annotations

import logging
import os
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.document import Document
from repositories.document_repository import DocumentRepository
from repositories.ocr_result_repository import OCRResultRepository
from schemas.document import DocumentCreate
from services.ocr_service import OCRService
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Orchestrates the full upload → OCR → persist pipeline.

    Responsibilities:
      1. Validate + save uploaded file to disk (FileHandler)
      2. Insert a Document row with status="pending"
      3. Run OCR (OCRService)
      4. Persist per-page OCRResult rows
      5. Update Document with aggregated OCR data and status="completed"
         (or status="failed" on error)
    """

    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.ocr_repo = OCRResultRepository(db)
        self.file_handler = FileHandler()
        self.ocr_service = OCRService()

    # ── Upload + OCR ───────────────────────────────────────────────────────────

    async def upload_and_extract(self, file: UploadFile, user_id: int) -> Document:
        """
        Full pipeline: receive uploaded file → OCR → return completed Document.
        On OCR failure the Document is still returned with status="failed".
        """
        # 1. Save file to disk
        saved = await self.file_handler.save(file)

        # 2. Create document row (status = "pending")
        doc_data = DocumentCreate(
            filename=saved["filename"],
            original_filename=saved["original_filename"],
            file_path=saved["file_path"],
            file_size=saved["file_size"],
            file_type=saved["file_type"],
            mime_type=saved["mime_type"],
            user_id=user_id,
        )
        document = self.doc_repo.create(doc_data)
        logger.info("document_service: created document id=%d", document.id)

        # 3. Run OCR
        document = self.doc_repo.set_processing(document.id)
        ocr_result = self.ocr_service.extract_from_file(saved["file_path"])

        if ocr_result.status == "failed":
            logger.error(
                "document_service: OCR failed for doc id=%d: %s",
                document.id, ocr_result.error,
            )
            document = self.doc_repo.set_failed(document.id, ocr_result.error or "Unknown error")
            return document

        # 4. Store per-page OCR rows
        if ocr_result.pages:
            self.ocr_repo.create_bulk(document.id, ocr_result.pages)

        # 5. Update document with aggregated results
        document = self.doc_repo.set_completed(
            document.id,
            extracted_text=ocr_result.full_text,
            total_pages=ocr_result.total_pages,
            average_confidence=ocr_result.average_confidence,
        )
        logger.info(
            "document_service: OCR complete doc id=%d pages=%d avg_conf=%.1f",
            document.id, ocr_result.total_pages, ocr_result.average_confidence,
        )
        return document

    # ── Read operations ────────────────────────────────────────────────────────

    def get_all(self, skip: int = 0, limit: int = 100, user_id: int|None = None) -> List[Document]:
        return self.doc_repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, doc_id: int) -> Document|None:
        return self.doc_repo.get_by_id(doc_id)

    def get_pages(self, doc_id: int):
        """Return the OCR page rows for a document."""
        return self.ocr_repo.get_by_document_id(doc_id)

    # ── Delete ─────────────────────────────────────────────────────────────────

    def delete(self, doc_id: int) -> bool:
        doc = self.doc_repo.get_by_id(doc_id)
        if not doc:
            return False
        # Remove file from disk
        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except OSError as exc:
            logger.warning("document_service: could not delete file %s: %s", doc.file_path, exc)
        # DB rows cascade-delete via FK
        return self.doc_repo.delete(doc_id)