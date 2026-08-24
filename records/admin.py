from django.contrib import admin

from records.models import ExtractedRecord


@admin.register(ExtractedRecord)
class ExtractedRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "original_name", "schema_name", "event", "status", "updated_at")
    list_filter = ("event", "status")
    search_fields = ("original_name", "schema_name")
