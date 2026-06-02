# backend/utils/pdf_converter.py
import logging
import tempfile
import os
from pathlib import Path

import cv2
import numpy as np
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class PDFConverter:

    def __init__(self, dpi: int = 200):
        self.dpi = dpi

    def convert_file(self, file_path: str) -> list[np.ndarray]:
        """
        Convert every page of a PDF to a list of cv2 images (BGR numpy arrays).
        Raises RuntimeError if conversion fails or the file produces no pages.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.debug(f"pdf_converter: converting {path.name} at {self.dpi} DPI")

        try:
            pil_images = convert_from_path(str(path), dpi=self.dpi)
        except Exception as exc:
            raise RuntimeError(f"pdf2image failed on {path.name}: {exc}") from exc

        if not pil_images:
            raise RuntimeError(f"pdf2image returned no pages for {path.name}")

        cv2_images: list[np.ndarray] = []
        for pil_img in pil_images:
            rgb = np.array(pil_img.convert("RGB"))
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            cv2_images.append(bgr)

        logger.debug(f"pdf_converter: converted {len(cv2_images)} page(s) from {path.name}")
        return cv2_images