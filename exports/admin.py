from django.contrib import admin

from .models import ExportBatch, WebhookDestination


@admin.register(ExportBatch)
class ExportBatchAdmin(admin.ModelAdmin):
    list_display = ("filename", "format", "row_count", "status", "created_at")
    list_filter = ("format", "status")


@admin.register(WebhookDestination)
class WebhookDestinationAdmin(admin.ModelAdmin):
    list_display = ("url", "last_status", "updated_at")
