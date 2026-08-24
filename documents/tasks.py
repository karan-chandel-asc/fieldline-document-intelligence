from celery import shared_task

from fieldline.logger import logger


@shared_task(name="documents.process_extraction_job")
def process_extraction_job(job_id):
    from documents.pipelines.document_pipeline import DocumentPipeline

    try:
        success, message, payload = DocumentPipeline().process_job(job_id)
        if not success:
            logger.error(f"Extraction job {job_id}: {message}")
        return {"success": success, "message": message, "job_id": job_id}
    except Exception as e:
        logger.error(f"Extraction job {job_id} crashed: {e}")
        raise


@shared_task(name="documents.process_single_document")
def process_single_document(document_id):
    from documents.pipelines.document_pipeline import DocumentPipeline

    try:
        success, message, payload = DocumentPipeline().process_retry_run(document_id)
        if not success:
            logger.error(f"Document retry {document_id}: {message}")
        return {"success": success, "message": message, "document_id": document_id}
    except Exception as e:
        logger.error(f"Document retry {document_id} crashed: {e}")
        raise
