from rest_framework import serializers

from documents.models import Document, ExtractionJob


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "original_name", "status", "error_message")
        read_only_fields = fields


class DocumentListSerializer(serializers.ModelSerializer):
    schema_name = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    received = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "original_name",
            "status",
            "schema_name",
            "summary",
            "received",
            "error_message",
        )
        read_only_fields = fields

    def get_schema_name(self, obj):
        return obj.schema.schema_name if obj.schema else ""

    def get_summary(self, obj):
        data = obj.extracted_data or {}
        for key in ("vendor", "merchant", "shipper", "consignee"):
            value = data.get(key)
            if value:
                return str(value)
        for value in data.values():
            if value not in (None, ""):
                return str(value)
        if obj.error_message:
            return obj.error_message
        if obj.status == Document.STATUS_QUEUED:
            return "Waiting in queue"
        if obj.status == Document.STATUS_PROCESSING:
            return "Extracting with Groq"
        return self.get_schema_name(obj) or "—"

    def get_received(self, obj):
        if not obj.created_at:
            return ""
        return obj.created_at.strftime("%d %b · %H:%M")


class ExtractionJobSerializer(serializers.ModelSerializer):
    schema_name = serializers.SerializerMethodField()
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = ExtractionJob
        fields = (
            "id",
            "status",
            "schema_name",
            "total_files",
            "processed",
            "success_count",
            "flagged_count",
            "error_message",
            "documents",
        )
        read_only_fields = fields

    def get_schema_name(self, obj):
        return obj.schema.schema_name if obj.schema else ""
