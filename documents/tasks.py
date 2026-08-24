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
