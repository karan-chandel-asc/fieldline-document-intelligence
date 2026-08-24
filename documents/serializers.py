import re

from rest_framework import serializers

from documents.models import Document, ExtractionJob
from documents.samples import build_sql

PG_TYPES = {
    "string": "text",
    "number": "numeric",
    "boolean": "boolean",
    "date": "date",
    "time": "time",
    "datetime": "timestamp",
    "array": "jsonb",
}


def schema_table_name(schema_name):
    slug = re.sub(r"[^a-z0-9]+", "_", (schema_name or "document").lower()).strip("_")
    return f"{slug or 'document'}_extract"


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "original_name", "status", "error_message")
        read_only_fields = fields


class DocumentListSerializer(serializers.ModelSerializer):
    schema_name = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    received = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

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
            "file_url",
        )
        read_only_fields = fields

    def get_schema_name(self, obj):
        return obj.schema.schema_name if obj.schema else "Auto extract"

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

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class DocumentDetailSerializer(DocumentListSerializer):
    schema_id = serializers.IntegerField(read_only=True, allow_null=True)
    schema_fields = serializers.SerializerMethodField()
    payload = serializers.SerializerMethodField()
    sql = serializers.SerializerMethodField()
    postgres = serializers.SerializerMethodField()

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + (
            "schema_id",
            "schema_fields",
            "extracted_data",
            "payload",
            "sql",
            "postgres",
        )

    def get_schema_fields(self, obj):
        if not obj.schema:
            return []
        return obj.schema.schema_fields or []

    def get_payload(self, obj):
        data = obj.extracted_data if isinstance(obj.extracted_data, dict) else {}
        payload = {
            "document_id": obj.id,
            "filename": obj.original_name,
            "schema": obj.schema.schema_name if obj.schema else "",
            "status": obj.status,
        }
        payload.update(data)
        return payload

    def get_sql(self, obj):
        table = schema_table_name(obj.schema.schema_name if obj.schema else "document")
        return build_sql(table, self.get_payload(obj))

    def get_postgres(self, obj):
        table = schema_table_name(obj.schema.schema_name if obj.schema else "document")
        fields = self.get_schema_fields(obj)
        if not fields:
            data = obj.extracted_data if isinstance(obj.extracted_data, dict) else {}
            cols = [
                f"  {key} text"
                for key, value in data.items()
                if not isinstance(value, (list, dict))
            ]
        else:
            cols = []
            for field in fields:
                name = re.sub(r"[^a-z0-9_]+", "_", str(field.get("field_name") or "").lower()).strip("_")
                if not name:
                    continue
                pg_type = PG_TYPES.get(str(field.get("field_type") or "string").lower(), "text")
                required = " NOT NULL" if field.get("field_required") else ""
                cols.append(f"  {name} {pg_type}{required}")
        body = ",\n".join(cols) if cols else "  payload jsonb"
        return f"CREATE TABLE {table} (\n  document_id integer PRIMARY KEY,\n{body}\n);"


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
        return obj.schema.schema_name if obj.schema else "Auto extract"
