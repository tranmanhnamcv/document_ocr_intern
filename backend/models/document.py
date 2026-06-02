from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # ── File metadata ─────────────────────────────────────────────────────────
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    owner = relationship("User", back_populates="documents")
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)          # bytes
    file_type = Column(String(50), nullable=True)       # "image" | "pdf"
    mime_type = Column(String(100), nullable=True)

    # ── OCR results (aggregated) ──────────────────────────────────────────────
    # Populated after OCR completes; NULL while status is "pending"/"processing"
    extracted_text = Column(Text, nullable=True)
    total_pages = Column(Integer, nullable=True)
    average_confidence = Column(Float, nullable=True)

    # ── Full-text search ──────────────────────────────────────────────────────
    # Built from original_filename (weight A) + extracted_text (weight B)
    # Updated by set_completed() in the repository; NULL until OCR finishes
    search_vector = Column(TSVECTOR, nullable=True)

    # ── Processing status ─────────────────────────────────────────────────────
    # "pending" → "processing" → "completed" | "failed"
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    ocr_results = relationship(
        "OCRResult",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="OCRResult.page_number",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_documents_search_vector", "search_vector", postgresql_using="gin"),
    )