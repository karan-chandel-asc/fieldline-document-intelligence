from django.contrib import admin

from .models import Document, ExtractionJob


@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "total_files", "processed", "created_by", "created_at")
    list_filter = ("status",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "original_name", "status", "job", "created_at")
    list_filter = ("status",)
