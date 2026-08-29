"""
Image preprocessing utilities using OpenCV.
Prepares images for optimal Tesseract OCR accuracy.

Pipelines:
    High-quality (clean PDFs, digital renders):
        1. Grayscale conversion
        2. Upscale if needed
        3. Otsu binarization

    Low-quality (scans, phone photos, faxes):
        1. Grayscale conversion
        2. Upscale if needed
        3. Deskew (rotation correction)
        4. Noise removal (median blur)
        5. Adaptive thresholding
        6. Morphological cleanup

Quality is assessed automatically via Laplacian variance, contrast, and
brightness. The routing decision is logged so thresholds can be tuned.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ─── Quality thresholds ──────────────────────────────────────────────────────
SHARPNESS_THRESHOLD: float = 20.0   # Laplacian variance
CONTRAST_THRESHOLD: float = 10.0    # pixel std-dev
BRIGHTNESS_MIN: float = 40.0        # mean pixel – too dark
BRIGHTNESS_MAX: float = 250.0       # mean pixel – overexposed


# ─── Data classes ─────────────────────────────────────────────────────────────
@dataclass
class ImageQualityReport:
    sharpness: float
    contrast: float
    brightness: float
    is_high_quality: bool
    reason: str
    pipeline: str   # "HIGH" | "LOW"

    def as_dict(self) -> dict:
        return asdict(self)


# ─── Module-level helper (used by the debug endpoint) ─────────────────────────
def assess_quality(image: np.ndarray, is_pdf: bool = False) -> ImageQualityReport:
    """Thin wrapper so callers don't need to instantiate ImageProcessor."""
    return ImageProcessor()._assess(image, is_pdf=is_pdf)


# ─── Main class ───────────────────────────────────────────────────────────────
class ImageProcessor:
    """
    Adaptive image preprocessor.

    High-quality images  →  Otsu binarisation only (no blur, no morph).
    Low-quality images   →  deskew → median blur → adaptive threshold → morph close.
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def preprocess(self, image: np.ndarray, is_pdf: bool = False) -> Tuple[np.ndarray, ImageQualityReport]:
        """
        Assess quality then route to the appropriate pipeline.

        Returns
        -------
        processed : np.ndarray   – grayscale, binarised image ready for Tesseract
        quality   : ImageQualityReport
        """
        gray = self._to_gray(image)
        quality = self._assess(image, is_pdf=is_pdf)

        if quality.is_high_quality:
            logger.debug("image_processor: HIGH quality → Otsu pipeline")
            processed = self._high_quality_pipeline(gray)
        else:
            logger.debug(
                "image_processor: LOW quality (%s) → full pipeline", quality.reason
            )
            processed = self._low_quality_pipeline(gray)

        return processed, quality

    # ── Quality assessment ────────────────────────────────────────────────────

    def _assess(self, image: np.ndarray, is_pdf: bool = False) -> ImageQualityReport:
        gray = self._to_gray(image)

        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        contrast = float(gray.std())
        brightness = float(gray.mean())

        reasons: list[str] = []

        if sharpness < SHARPNESS_THRESHOLD:
            reasons.append(
                f"blurry (sharpness={sharpness:.1f} < {SHARPNESS_THRESHOLD})"
            )
        if contrast < CONTRAST_THRESHOLD:
            reasons.append(
                f"low contrast (contrast={contrast:.1f} < {CONTRAST_THRESHOLD})"
            )
        if brightness < BRIGHTNESS_MIN:
            reasons.append(
                f"too dark (brightness={brightness:.1f} < {BRIGHTNESS_MIN})"
            )
        if not is_pdf and brightness > BRIGHTNESS_MAX:
            reasons.append(
                f"overexposed (brightness={brightness:.1f} > {BRIGHTNESS_MAX})"
            )

        is_high_quality = len(reasons) == 0
        reason = "OK" if is_high_quality else "; ".join(reasons)
        pipeline = "HIGH" if is_high_quality else "LOW"

        return ImageQualityReport(
            sharpness=round(sharpness, 2),
            contrast=round(contrast, 2),
            brightness=round(brightness, 2),
            is_high_quality=is_high_quality,
            reason=reason,
            pipeline=pipeline,
        )

    # ── Pipelines ─────────────────────────────────────────────────────────────

    def _high_quality_pipeline(self, gray: np.ndarray) -> np.ndarray:
        """Otsu binarisation only – preserves thin strokes in clean PDF renders."""
        _, binarised = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binarised

    def _low_quality_pipeline(self, gray: np.ndarray) -> np.ndarray:
        """
        Full correction pipeline for scans / phone photos:
          1. Deskew
          2. Median blur (denoise)
          3. Adaptive threshold
          4. Morph close (close tiny gaps)
        """
        deskewed = self._deskew(gray)
        denoised = cv2.medianBlur(deskewed, 3)
        thresholded = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31,
            C=10,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morphed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
        return morphed

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image.copy()

    @staticmethod
    def _deskew(gray: np.ndarray) -> np.ndarray:
        """Rotate image to correct skew using minAreaRect on dark pixel coords."""
        coords = np.column_stack(np.where(gray < 128))[:, ::-1]
        if len(coords) < 10:
            # Not enough dark pixels to estimate skew; return as-is
            return gray

        angle = cv2.minAreaRect(coords)[-1]
        if angle > 45:
            angle = angle -90
        angle = -angle

        if abs(angle) > 15:
            # Implausibly large skew estimate — almost always an estimation
            # error rather than a genuinely rotated page. Skip correction.
            logger.debug("image_processor: skipping deskew, implausible angle %.2f°", angle)
            return gray
        
        if abs(angle) < 0.5:
            # Skew is negligible
            return gray

        h, w = gray.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            gray, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        logger.debug("image_processor: deskewed by %.2f°", angle)
        return rotated