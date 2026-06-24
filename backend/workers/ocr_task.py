from workers.celery_app import celery_app
from core.database import SessionLocal
from services.ocr_service import OCRService
from repositories.document_repository import DocumentRepository
from repositories.ocr_result_repository import OCRResultRepository


@celery_app.task(name="workers.ocr_task.process_ocr")
def process_ocr(document_id: int, file_path: str):
    """
    Background task: runs the full OCR pipeline for a document.
    Called after the file has been saved and the DB row created as 'pending'.
    """
    db = SessionLocal()
    try:
        doc_repo = DocumentRepository(db)
        ocr_result_repo = OCRResultRepository(db)
        ocr_service = OCRService()

        doc_repo.set_processing(document_id)

        ocr_result = ocr_service.extract_from_file(file_path)

        if ocr_result.status == "failed":
            doc_repo.set_failed(document_id, ocr_result.error or "OCR failed")
        else:
            if ocr_result.pages:
                ocr_result_repo.create_bulk(document_id, ocr_result.pages)
            doc_repo.set_completed(
                document_id,
                extracted_text=ocr_result.full_text,
                total_pages=ocr_result.total_pages,
                average_confidence=ocr_result.average_confidence,
            )

    except Exception as e:
        try:
            doc_repo.set_failed(document_id, str(e))
        except Exception:
            pass
    finally:
        db.close()