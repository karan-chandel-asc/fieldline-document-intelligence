from django.utils import timezone

from documents.models import Document
from exports.models import ExportBatch
from fieldline.logger import logger


class DashboardService:
    def _owned(self, queryset, user):
        if getattr(user, "is_authenticated", False):
            return queryset.filter(created_by=user)
        return queryset.filter(created_by__isnull=True)

    def get_overview(self, user=None):
        try:
            docs = self._owned(Document.objects.select_related("schema"), user)
            queued = docs.filter(
                status__in=[Document.STATUS_QUEUED, Document.STATUS_PROCESSING]
            ).count()
            needs_review = docs.filter(status=Document.STATUS_NEEDS_REVIEW).count()
            exceptions = docs.filter(status=Document.STATUS_FAILED).count()
            today = timezone.now().date()
            extracted_today = docs.filter(
                status=Document.STATUS_NEEDS_REVIEW,
                created_at__date=today,
            ).count()
            attention = list(
                docs.filter(status=Document.STATUS_NEEDS_REVIEW).order_by("-created_at")[:5]
            )
            export_count = self._owned(ExportBatch.objects.all(), user).count()
            if queued:
                pipeline_step = 3
            elif needs_review:
                pipeline_step = 4
            elif export_count:
                pipeline_step = 5
            elif docs.exists():
                pipeline_step = 3
            else:
                pipeline_step = 1
            return True, "Overview fetched", {
                "queued": queued,
                "needs_review": needs_review,
                "extracted_today": extracted_today,
                "exceptions": exceptions,
                "pipeline_step": pipeline_step,
                "attention": attention,
            }
        except Exception as e:
            logger.error(f"Error building dashboard overview: {e}")
            return False, f"Error building dashboard overview: {e}", None
