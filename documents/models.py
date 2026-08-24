from django.conf import settings
from django.db import models


def document_upload_to(instance, filename):
    job_id = instance.job_id or "pending"
    return f"documents/{job_id}/{filename}"


class ExtractionJob(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    schema = models.ForeignKey(
        "schemas.Schema",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extraction_jobs",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="extraction_jobs",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    total_files = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    flagged_count = models.PositiveIntegerField(default=0)
    celery_task_id = models.CharField(max_length=80, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job {self.pk} ({self.status})"


class Document(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_PROCESSING = "processing"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_EXTRACTED = "extracted"
    STATUS_APPROVED = "approved"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_NEEDS_REVIEW, "Needs review"),
        (STATUS_EXTRACTED, "Extracted"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_FAILED, "Failed"),
    ]

    job = models.ForeignKey(ExtractionJob, on_delete=models.CASCADE, related_name="documents")
    schema = models.ForeignKey(
        "schemas.Schema",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    file = models.FileField(upload_to=document_upload_to)
    original_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    extracted_data = models.JSONField(default=dict, blank=True)
    field_meta = models.JSONField(default=dict, blank=True)
    page_images = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name
