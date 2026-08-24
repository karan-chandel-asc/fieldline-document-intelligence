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
