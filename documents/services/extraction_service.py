from documents.models import Document, ExtractionJob
from documents.services.groq_extraction import GroqExtractionService
from fieldline.logger import logger


class ExtractionService:
    def __init__(self):
        self.groq_extraction = GroqExtractionService()

    def process_job(self, job_id):
        try:
            job = ExtractionJob.objects.filter(pk=job_id).select_related("schema").first()
            if not job:
                return False, "Job not found", None

            job.status = ExtractionJob.STATUS_PROCESSING
            job.error_message = ""
            job.save(update_fields=["status", "error_message", "updated_at"])

            for document in job.documents.all().order_by("id"):
                self.process_document(document, job)

            job.refresh_from_db()
            job.status = ExtractionJob.STATUS_COMPLETED
            job.save(update_fields=["status", "updated_at"])
            return True, "Job completed", job
        except Exception as e:
            logger.error(f"Error processing extraction job: {e}")
            ExtractionJob.objects.filter(pk=job_id).update(
                status=ExtractionJob.STATUS_FAILED,
                error_message=str(e),
            )
            return False, f"Error processing extraction job: {e}", None

    def process_document(self, document, job):
        document.status = Document.STATUS_PROCESSING
        document.save(update_fields=["status", "updated_at"])
        try:
            text = self.groq_extraction.extract_text(document.file.path)
            success, message, data = self.groq_extraction.extract_fields(job.schema, text)
            if not success:
                document.status = Document.STATUS_FAILED
                document.error_message = message
                document.extracted_data = {}
                document.save(update_fields=["status", "error_message", "extracted_data", "updated_at"])
                job.processed += 1
                job.flagged_count += 1
                job.save(update_fields=["processed", "flagged_count", "updated_at"])
                return False, message, document

            document.status = Document.STATUS_NEEDS_REVIEW
            document.error_message = ""
            document.extracted_data = data or {}
            document.save(update_fields=["status", "error_message", "extracted_data", "updated_at"])
            job.processed += 1
            job.success_count += 1
            job.save(update_fields=["processed", "success_count", "updated_at"])
            return True, message, document
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}")
            document.status = Document.STATUS_FAILED
            document.error_message = str(e)
            document.save(update_fields=["status", "error_message", "updated_at"])
            job.processed += 1
            job.flagged_count += 1
            job.save(update_fields=["processed", "flagged_count", "updated_at"])
            return False, str(e), document
