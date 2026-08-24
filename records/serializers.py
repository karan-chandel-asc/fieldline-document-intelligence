from rest_framework import serializers

from records.models import ExtractedRecord


class ExtractedRecordSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(read_only=True, allow_null=True)
    received = serializers.SerializerMethodField()

    class Meta:
        model = ExtractedRecord
        fields = (
            "id",
            "document_id",
            "original_name",
            "schema_name",
            "event",
            "status",
            "payload",
            "webhook_status",
            "received",
        )
        read_only_fields = fields

    def get_received(self, obj):
        if not obj.updated_at:
            return ""
        return obj.updated_at.strftime("%d %b · %H:%M")
