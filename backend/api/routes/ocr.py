"""
OCR API routes.

Endpoints:
    POST /api/ocr/extract    — upload a file and return OCR text
    GET  /api/ocr/supported  — list accepted file types
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from schemas.ocr import OCRErrorSchema, OCRResponseSchema
from services.ocr_service import OCRService, IMAGE_EXTENSIONS, PDF_EXTENSIONS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

UPLOAD_DIR = Path("/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS
MAX_FILE_SIZE_MB = 20

_ocr_service = OCRService()


@router.post(
    "/extract",
    response_model=OCRResponseSchema,
    responses={
        400: {"model": OCRErrorSchema},
        500: {"model": OCRErrorSchema},
    },
    summary="Upload a file and extract text via OCR",
)
async def extract_text(file: UploadFile = File(...)):
    """
    Upload an image (JPEG, PNG, TIFF, BMP, WebP) or PDF and receive
    the extracted text along with per-page confidence scores.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{suffix}'. Accepted: {sorted(ALLOWED_EXTENSIONS)}",
        )

    unique_name = f"{uuid.uuid4().hex}{suffix}"
    save_path = UPLOAD_DIR / unique_name

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_mb = save_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large ({file_size_mb:.1f} MB). Max: {MAX_FILE_SIZE_MB} MB.",
            )

        result = _ocr_service.extract(save_path)

        if not result.succeeded:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"filename": file.filename, "error": result.error or "No text extracted"},
            )

        return OCRResponseSchema(
            filename=file.filename or unique_name,
            file_type=result.file_type,
            total_pages=result.total_pages,
            full_text=result.full_text,
            pages=[
                {
                    "page_number": p.page_number,
                    "text": p.text,
                    "confidence": p.confidence,
                    "word_count": p.word_count,
                }
                for p in result.pages
            ],
            avg_confidence=result.avg_confidence,
            processing_time_ms=result.processing_time_ms,
            succeeded=result.succeeded,
        )

    finally:
        if save_path.exists():
            save_path.unlink()


@router.get("/supported", summary="List supported file types")
async def supported_formats():
    return {
        "images": sorted(IMAGE_EXTENSIONS),
        "documents": sorted(PDF_EXTENSIONS),
    }