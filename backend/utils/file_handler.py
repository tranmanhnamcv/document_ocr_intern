from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from core.config import settings

logger = logging.getLogger(__name__)

# Allowed MIME types → file_type label
ALLOWED_TYPES: dict[str, str] = {
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "image/tiff": "image",
    "image/bmp": "image",
    "image/webp": "image",
    "application/pdf": "pdf",
}

MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class FileHandler:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile) -> dict:
        """
        Validate and persist an uploaded file.

        Returns a dict with keys:
            filename, original_filename, file_path,
            file_size, file_type, mime_type
        """
        # ── Validate MIME type ────────────────────────────────────────────────
        mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
        file_type = ALLOWED_TYPES.get(mime)
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type: {mime}. "
                    f"Allowed types: {', '.join(ALLOWED_TYPES)}"
                ),
            )

        # ── Read content ──────────────────────────────────────────────────────
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if file_size > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size / 1_048_576:.1f} MB). Max is 50 MB.",
            )

        # ── Build a unique filename ───────────────────────────────────────────
        ext = Path(file.filename or "file").suffix.lower() or self._ext_from_mime(mime)
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = self.upload_dir / unique_name

        # ── Write to disk ─────────────────────────────────────────────────────
        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except OSError as exc:
            logger.exception("file_handler: failed to write %s", file_path)
            raise HTTPException(status_code=500, detail=f"Could not save file: {exc}")

        logger.info(
            "file_handler: saved %s → %s (%d bytes)",
            file.filename, file_path, file_size,
        )

        return {
            "filename": unique_name,
            "original_filename": file.filename or unique_name,
            "file_path": str(file_path),
            "file_size": file_size,
            "file_type": file_type,
            "mime_type": mime,
        }

    @staticmethod
    def _ext_from_mime(mime: str) -> str:
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/tiff": ".tiff",
            "image/bmp": ".bmp",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
        }
        return mapping.get(mime, "")