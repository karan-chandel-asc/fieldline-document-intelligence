from accounts.pipelines.base_pipeline import BasePipeline
from documents.services.extraction_service import ExtractionService
from documents.services.upload_service import DocumentUploadService
from fieldline.logger import logger


class DocumentPipeline(BasePipeline):
    def __init__(self):
        self.upload_service = DocumentUploadService()
        self.extraction_service = ExtractionService()

    def process_item(self, data):
        return self.process_upload(data.get("files"), data.get("schema_id"), data.get("user"))

    def process_upload(self, files, schema_id, user=None):
        try:
            success, message, payload = self.upload_service.queue_upload(
                files, schema_id, user=user
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_upload: {e}")
            return False, f"Error in process_upload: {e}", None

    def process_job_status(self, job_id, user=None):
        try:
            success, message, payload = self.upload_service.get_job(job_id, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_job_status: {e}")
            return False, f"Error in process_job_status: {e}", None

    def process_job(self, job_id):
        try:
            success, message, payload = self.extraction_service.process_job(job_id)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_job: {e}")
            return False, f"Error in process_job: {e}", None

    def process_list(self, user=None, search="", status="all", schema_id=None, received=""):
        try:
            success, message, payload = self.upload_service.list_documents(
                user=user,
                search=search,
                status=status,
                schema_id=schema_id,
                received=received,
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_list: {e}")
            return False, f"Error in process_list: {e}", None

    def process_get(self, document_id, user=None):
        try:
            success, message, payload = self.upload_service.get_document(document_id, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_get: {e}")
            return False, f"Error in process_get: {e}", None

    def process_update(self, document_id, data, user=None):
        try:
            success, message, payload = self.upload_service.update_document(
                document_id, data, user=user
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_update: {e}")
            return False, f"Error in process_update: {e}", None

    def process_retry(self, document_id, user=None):
        try:
            success, message, payload = self.upload_service.retry_document(
                document_id, user=user
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_retry: {e}")
            return False, f"Error in process_retry: {e}", None

    def process_retry_run(self, document_id):
        try:
            success, message, payload = self.extraction_service.retry_document(document_id)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_retry_run: {e}")
            return False, f"Error in process_retry_run: {e}", None
