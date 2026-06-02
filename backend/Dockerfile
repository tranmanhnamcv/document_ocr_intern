# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# System deps:
#   tesseract-ocr    — OCR engine
#   poppler-utils    — pdf2image (pdfinfo + pdftoppm)
#   libgl1           — OpenCV headless still needs this on some distros
#   libglib2.0-0     — OpenCV runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-vie \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Stage 2: dependencies ─────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install -r requirements.txt

# ── Stage 3: application ──────────────────────────────────────────────────────
COPY . .


# Expose the FastAPI port
EXPOSE 9000

# Run with uvicorn; --reload for development (remove for production)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]