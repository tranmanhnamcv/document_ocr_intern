from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Tuple

import cv2
import numpy as np
import pytesseract

from utils.image_processor import ImageProcessor, ImageQualityReport
from utils.pdf_converter import PDFConverter
from schemas.ocr_result import PageResult

logger = logging.getLogger(__name__)

# ─── Tesseract config ─────────────────────────────────────────────────────────
TESSERACT_CONFIG = "--oem 3 --psm 3"


# ─── Result data classes ──────────────────────────────────────────────────────

@dataclass
class OCRResult:
    pages: List[PageResult] = field(default_factory=list)
    full_text: str = ""
    average_confidence: float = 0.0
    total_pages: int = 0
    status: str = "completed"   # "completed" | "failed"
    error: str|None = None

    def finalize(self) -> None:
        """Calculate aggregate fields from individual page results."""
        self.total_pages = len(self.pages)
        self.full_text = "\n\n".join(p.text for p in self.pages).strip()

        confidences = [p.confidence for p in self.pages if p.confidence > 0]
        self.average_confidence = (
            round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        )


# ─── Service ──────────────────────────────────────────────────────────────────
class OCRService:
    """
    Orchestrates the full OCR pipeline:
      file path → PDFConverter / cv2.imread → ImageProcessor → Tesseract → OCRResult
    """

    def __init__(self, dpi: int = 200):
        self.dpi = dpi
        self.processor = ImageProcessor()
        self.pdf_converter = PDFConverter(dpi=dpi)

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_from_file(self, file_path: str) -> OCRResult:
        """
        Entry point: detect file type and dispatch to the right extractor.
        Always returns an OCRResult – errors are captured inside it.
        """
        try:
            if file_path.lower().endswith(".pdf"):
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)
        except Exception as exc:
            logger.exception("ocr_service: extraction failed for %s", file_path)
            result = OCRResult(status="failed", error=str(exc))
            return result

    # ── Extractors ────────────────────────────────────────────────────────────

    def _extract_from_image(self, file_path: str) -> OCRResult:
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"cv2.imread returned None for path: {file_path}")

        processed, quality = self.processor.preprocess(image)
        text, confidence = self._run_tesseract(processed, quality, page_num=1)

        page = PageResult(
            page_number=1,
            text=text,
            confidence=confidence,
            quality_report=quality.as_dict(),
        )
        result = OCRResult(pages=[page])
        result.finalize()
        return result

    def _extract_from_pdf(self, file_path: str) -> OCRResult:
        images = self.pdf_converter.convert_file(file_path)
        if not images:
            raise ValueError(f"PDFConverter produced no pages for: {file_path}")

        result = OCRResult()
        for i, image in enumerate(images, start=1):
            processed, quality = self.processor.preprocess(image, is_pdf=True)
            text, confidence = self._run_tesseract(processed, quality, page_num=i)

            page = PageResult(
                page_number=i,
                text=text,
                confidence=confidence,
                quality_report=quality.as_dict(),
            )
            result.pages.append(page)
            logger.info(
                "ocr_service: page %d/%d — pipeline=%s confidence=%.1f",
                i, len(images), quality.pipeline, confidence,
            )

        result.finalize()
        return result

    # ── Tesseract wrapper ─────────────────────────────────────────────────────

    def _run_tesseract(
        self,
        image: np.ndarray,
        quality: ImageQualityReport,
        page_num: int = 1,
    ) -> Tuple[str, float]:
        """
        Run Tesseract on a pre-processed image.

        Returns
        -------
        text       : str   – extracted text
        confidence : float – mean word confidence (0–100)
        """
        logger.debug(
            "ocr_service: page %d pipeline=%s reason=%s",
            page_num, quality.pipeline, quality.reason,
        )

        # image_to_string for the text
        text: str = pytesseract.image_to_string(
            image, config=TESSERACT_CONFIG
        ).strip()

        # image_to_data for per-word confidence scores
        data = pytesseract.image_to_data(
            image,
            config=TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT,
        )

        valid_confs: List[float] = [
            float(conf)
            for conf, word in zip(data["conf"], data["text"])
            if word.strip() and conf != -1
        ]
        confidence = round(sum(valid_confs) / len(valid_confs), 2) if valid_confs else 0.0

        return text, confidence