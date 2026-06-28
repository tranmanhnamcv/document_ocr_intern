from __future__ import annotations

import logging
import os
import tempfile

import cv2
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from core.database import get_db
from models.user import User
from schemas.document import DocumentDetailResponse, DocumentResponse, UploadResponse
from services.document_service import DocumentService
from utils.image_processor import assess_quality
from utils.pdf_converter import PDFConverter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


# ─── Dependencies ─────────────────────────────────────────────────────────────
def get_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


# ─── Upload + OCR ─────────────────────────────────────────────────────────────
@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    document = await service.upload_and_extract(file, user_id=current_user.id)
    return UploadResponse(
        message="File uploaded and OCR extraction complete.",
        document=document,
    )


# ─── List documents ───────────────────────────────────────────────────────────
@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    service: DocumentService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_all(skip=skip, limit=limit, user_id=current_user.id)


# ─── Get single document (with pages) ────────────────────────────────────────
@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(
    doc_id: int,
    service: DocumentService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    doc = service.get_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    pages = service.get_pages(doc_id)
    response = DocumentDetailResponse.model_validate(doc)
    response.pages = pages
    return response


# ─── Delete document ──────────────────────────────────────────────────────────
@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    service: DocumentService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    doc = service.get_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    service.delete(doc_id)


# ─── Debug: quality assessment (no auth — dev only) ──────────────────────────
# TODO: Remove before production deployment
@router.post("/debug/quality")
async def debug_quality(file: UploadFile = File(...)):
    """
    DEV ONLY — assess image quality metrics without running full OCR.
    Accepts an image or PDF. For PDFs, only page 1 is assessed.
    """
    import numpy as np

    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            converter = PDFConverter(dpi=150)
            pages = converter.convert_file(tmp_path)
            if not pages:
                raise HTTPException(status_code=400, detail="PDF has no pages.")
            image = pages[0]
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not read PDF: {exc}")
        finally:
            os.unlink(tmp_path)
    else:
        buf = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Could not decode image. Ensure it is a valid JPEG/PNG/TIFF/BMP/WEBP.",
            )

    report = assess_quality(image, is_pdf=filename.endswith(".pdf"))
    return report.as_dict()