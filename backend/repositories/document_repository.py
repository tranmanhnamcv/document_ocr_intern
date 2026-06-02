# backend/repositories/document_repository.py
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.document import Document
from schemas.document import DocumentCreate, SearchResultItem

logger = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_by_id(self, document_id: int) -> None|Document:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Document]:
        return (
            self.db.query(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ── Create ────────────────────────────────────────────────────────────────

    def create(self, doc_data: DocumentCreate) -> Document:
        doc = Document(
            filename=doc_data.filename,
            original_filename=doc_data.original_filename,
            file_path=doc_data.file_path,
            file_size=doc_data.file_size,
            file_type=doc_data.file_type,
            mime_type=doc_data.mime_type,
            status="pending",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        logger.info("document_repository: created document id=%d", doc.id)
        return doc

    # ── Status transitions ────────────────────────────────────────────────────

    def set_processing(self, document_id: int) -> None|Document:
        return self._update_fields(document_id, status="processing")

    def set_completed(
        self,
        document_id: int,
        extracted_text: str,
        total_pages: int,
        average_confidence: float,
    ) -> None|Document:
        doc = self.get_by_id(document_id)
        if not doc:
            logger.warning(
                "document_repository: set_completed — id=%d not found", document_id
            )
            return None

        doc.status = "completed"
        doc.extracted_text = extracted_text
        doc.total_pages = total_pages
        doc.average_confidence = average_confidence

        # Build search vector:
        #   weight A → original_filename (higher relevance in ranking)
        #   weight B → extracted_text
        doc.search_vector = func.setweight(
            func.to_tsvector("english", doc.original_filename), "A"
        ).op("||")(
            func.setweight(
                func.to_tsvector("english", extracted_text or ""), "B"
            )
        )

        self.db.commit()
        self.db.refresh(doc)
        logger.info(
            "document_repository: set_completed id=%d pages=%d",
            document_id, total_pages,
        )
        return doc

    def set_failed(
        self,
        document_id: int,
        error_message: str,
    ) -> None|Document:
        return self._update_fields(
            document_id,
            status="failed",
            error_message=error_message,
        )

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, document_id: int) -> bool:
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        logger.info("document_repository: deleted document id=%d", document_id)
        return True

    # ── Full-text search ──────────────────────────────────────────────────────

    def search(self, query: str, skip: int = 0, limit: int = 20) -> list[dict]:
        ts_query = func.plainto_tsquery("english", query)

        results = (
            self.db.query(
                Document,
                func.ts_rank(Document.search_vector, ts_query).label("rank"),
                func.ts_headline(
                    "english",
                    Document.extracted_text,
                    ts_query,
                    "MaxWords=35, MinWords=15, StartSel=<mark>, StopSel=</mark>",
                ).label("headline"),
            )
            .filter(Document.search_vector.op("@@")(ts_query))
            .filter(Document.status == "completed")
            .order_by(func.ts_rank(Document.search_vector, ts_query).desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {"document": doc, "rank": float(rank), "headline": headline}
            for doc, rank, headline in results
        ]

    def search_count(self, query: str) -> int:
        ts_query = func.plainto_tsquery("english", query)
        return (
            self.db.query(func.count(Document.id))
            .filter(Document.search_vector.op("@@")(ts_query))
            .filter(Document.status == "completed")
            .scalar()
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _update_fields(self, document_id: int, **kwargs) -> None | Document:
        doc = self.get_by_id(document_id)
        if not doc:
            logger.warning(
                "document_repository: _update_fields — id=%d not found", document_id
            )
            return None
        for key, value in kwargs.items():
            setattr(doc, key, value)
        self.db.commit()
        self.db.refresh(doc)
        logger.info(
            "document_repository: updated id=%d fields=%s",
            document_id, list(kwargs.keys()),
        )
        return doc