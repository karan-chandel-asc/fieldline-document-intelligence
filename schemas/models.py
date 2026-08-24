from django.conf import settings
from django.db import models


class Schema(models.Model):
    schema_name = models.CharField(max_length=160)
    schema_description = models.TextField(blank=True, default="")
    schema_fields = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="extraction_schemas",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.schema_name
