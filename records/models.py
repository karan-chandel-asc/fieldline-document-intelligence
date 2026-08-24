from django.conf import settings
from django.db import models


class ExtractedRecord(models.Model):
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extracted_records",
    )
    original_name = models.CharField(max_length=255)
    schema_name = models.CharField(max_length=160, blank=True, default="")
    event = models.CharField(max_length=80, default="fieldline.document.extracted")
    status = models.CharField(max_length=40, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    webhook_status = models.CharField(max_length=80, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="extracted_records",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.original_name
