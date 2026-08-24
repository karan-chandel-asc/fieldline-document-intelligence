from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from documents.models import Document, ExtractionJob
from fieldline.logger import logger
from schemas.models import Schema


class DocumentUploadService:
    def queue_upload(self, files, schema_id, user=None):
        try:
            if not files:
                return False, "Select at least one PDF", None

            schema = None
            if schema_id:
                schema = Schema.objects.filter(pk=schema_id).first()
                if not schema:
                    return False, "Schema not found", None

            created_by = user if getattr(user, "is_authenticated", False) else None
            pdfs = []
            for uploaded in files:
                name = (getattr(uploaded, "name", "") or "").lower()
                if not name.endswith(".pdf"):
                    return False, "Only PDF files are supported", None
                pdfs.append(uploaded)

            with transaction.atomic():
                job = ExtractionJob.objects.create(
                    schema=schema,
                    created_by=created_by,
                    total_files=len(pdfs),
                    status=ExtractionJob.STATUS_QUEUED,
                )
                for uploaded in pdfs:
                    document = Document(
                        job=job,
                        schema=schema,
                        original_name=uploaded.name,
                        created_by=created_by,
                        status=Document.STATUS_QUEUED,
                    )
                    document.file.save(uploaded.name, uploaded, save=True)

            return True, "Extraction queued", job
        except Exception as e:
            logger.error(f"Error queueing upload: {e}")
            return False, f"Error queueing upload: {e}", None

    def get_job(self, job_id, user=None):
        try:
            queryset = ExtractionJob.objects.filter(pk=job_id).prefetch_related("documents")
            if getattr(user, "is_authenticated", False):
                queryset = queryset.filter(created_by=user)
            else:
                queryset = queryset.filter(created_by__isnull=True)
            job = queryset.first()
            if not job:
                return False, "Job not found", None
            return True, "Job fetched", job
        except Exception as e:
            logger.error(f"Error fetching job: {e}")
            return False, f"Error fetching job: {e}", None

    def list_documents(self, user=None, search="", status="all", schema_id=None, received=""):
        try:
            queryset = Document.objects.select_related("schema").order_by("-created_at")
            if getattr(user, "is_authenticated", False):
                queryset = queryset.filter(created_by=user)
            else:
                queryset = queryset.filter(created_by__isnull=True)

            status_map = {
                "review": [Document.STATUS_NEEDS_REVIEW],
                "needs_review": [Document.STATUS_NEEDS_REVIEW],
                "queued": [Document.STATUS_QUEUED, Document.STATUS_PROCESSING],
                "processing": [Document.STATUS_PROCESSING],
                "extracted": [Document.STATUS_EXTRACTED],
                "approved": [Document.STATUS_APPROVED],
                "failed": [Document.STATUS_FAILED],
            }
            if status and status not in {"all", ""}:
                queryset = queryset.filter(status__in=status_map.get(status, [status]))

            if schema_id:
                queryset = queryset.filter(schema_id=schema_id)

            now = timezone.now()
            if received == "today":
                queryset = queryset.filter(created_at__date=now.date())
            elif received == "7d":
                queryset = queryset.filter(created_at__gte=now - timedelta(days=7))

            if search:
                queryset = queryset.filter(
                    Q(original_name__icontains=search)
                    | Q(schema__schema_name__icontains=search)
                    | Q(error_message__icontains=search)
                    | Q(extracted_data__icontains=search)
                ).distinct()

            return True, "Documents fetched", queryset
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return False, f"Error listing documents: {e}", None

    def _owned_documents(self, user=None):
        queryset = Document.objects.select_related("schema", "job")
        if getattr(user, "is_authenticated", False):
            return queryset.filter(created_by=user)
        return queryset.filter(created_by__isnull=True)

    def get_document(self, document_id, user=None):
        try:
            document = self._owned_documents(user).filter(pk=document_id).first()
            if not document:
                return False, "Document not found", None
            return True, "Document fetched", document
        except Exception as e:
            logger.error(f"Error fetching document: {e}")
            return False, f"Error fetching document: {e}", None

    def update_document(self, document_id, data, user=None):
        try:
            success, message, document = self.get_document(document_id, user=user)
            if not success:
                return False, message, None

            fields = []
            if data.get("extracted_data") is not None:
                if not isinstance(data["extracted_data"], dict):
                    return False, "extracted_data must be an object", None
                document.extracted_data = data["extracted_data"]
                fields.append("extracted_data")

            if data.get("schema_id"):
                schema = Schema.objects.filter(pk=data["schema_id"]).first()
                if not schema:
                    return False, "Schema not found", None
                document.schema = schema
                fields.append("schema")

            if data.get("status"):
                document.status = data["status"]
                fields.append("status")
                if data["status"] == Document.STATUS_FAILED:
                    document.error_message = data.get("error_message") or "Rejected"
                    fields.append("error_message")
                elif data["status"] in {Document.STATUS_APPROVED, Document.STATUS_NEEDS_REVIEW}:
                    document.error_message = ""
                    fields.append("error_message")

            if not fields:
                return False, "Nothing to update", None

            document.save(update_fields=fields + ["updated_at"])
            if document.status == Document.STATUS_APPROVED:
                try:
                    from records.services.webhook_dispatch import WebhookDispatchService

                    WebhookDispatchService().dispatch_document(
                        document, "fieldline.document.approved"
                    )
                except Exception as hook_error:
                    logger.error(f"Approved-data webhook failed: {hook_error}")
            return True, "Document updated", document
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False, f"Error updating document: {e}", None

    def retry_document(self, document_id, user=None):
        try:
            success, message, document = self.get_document(document_id, user=user)
            if not success:
                return False, message, None
            if document.status == Document.STATUS_PROCESSING:
                return False, "Document is already processing", None
            if not document.file:
                return False, "Original file is missing", None
            document.status = Document.STATUS_QUEUED
            document.error_message = ""
            document.save(update_fields=["status", "error_message", "updated_at"])
            return True, "Retry queued", document
        except Exception as e:
            logger.error(f"Error retrying document: {e}")
            return False, f"Error retrying document: {e}", None
