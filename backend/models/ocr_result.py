from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key back to the parent document
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Per-page OCR data
    page_number = Column(Integer, nullable=False, default=1)
    extracted_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    # Quality assessment stored as JSON so it is queryable / loggable
    quality_report = Column(JSON, nullable=True)
    pipeline_used = Column(String(10), nullable=True)   # "HIGH" | "LOW"

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to parent document (optional – handy for joins)
    document = relationship("Document", back_populates="ocr_results")