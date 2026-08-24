from django.contrib import admin

from .models import Schema


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("schema_name", "created_by", "created_at")
    search_fields = ("schema_name", "schema_description")
    list_filter = ("created_at",)
