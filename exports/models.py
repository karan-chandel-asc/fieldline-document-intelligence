from django.conf import settings
from django.db import models


def export_upload_to(instance, filename):
    return f"exports/{filename}"


class ExportBatch(models.Model):
    FORMAT_JSON = "json"
    FORMAT_CSV = "csv"
    FORMAT_CHOICES = [
        (FORMAT_JSON, "JSON"),
        (FORMAT_CSV, "CSV"),
    ]
    RANGE_TODAY = "today"
    RANGE_WEEK = "week"
    RANGE_ALL = "all"
    RANGE_CHOICES = [
        (RANGE_TODAY, "Extracted today"),
        (RANGE_WEEK, "This week"),
        (RANGE_ALL, "All extracted"),
    ]
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_READY, "Ready"),
        (STATUS_FAILED, "Failed"),
    ]

    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    source_range = models.CharField(max_length=12, choices=RANGE_CHOICES, default=RANGE_ALL)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=export_upload_to, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_READY)
    error_message = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="export_batches",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.filename


class WebhookDestination(models.Model):
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=255, blank=True, default="")
    last_status = models.CharField(max_length=80, blank=True, default="")
    last_tested_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webhook_destinations",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.url
