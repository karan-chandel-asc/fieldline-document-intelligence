from django.urls import reverse
from rest_framework import serializers

from exports.models import ExportBatch, WebhookDestination


class ExportBatchSerializer(serializers.ModelSerializer):
    created_label = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    range_label = serializers.SerializerMethodField()

    class Meta:
        model = ExportBatch
        fields = (
            "id",
            "filename",
            "format",
            "source_range",
            "range_label",
            "row_count",
            "status",
            "created_label",
            "download_url",
            "error_message",
        )
        read_only_fields = fields

    def get_created_label(self, obj):
        if not obj.created_at:
            return ""
        return obj.created_at.strftime("%d %b · %H:%M")

    def get_range_label(self, obj):
        return obj.get_source_range_display()

    def get_download_url(self, obj):
        return reverse("export_download_api", args=[obj.id])


class WebhookDestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDestination
        fields = ("id", "url", "last_status")
        read_only_fields = ("id", "last_status")
