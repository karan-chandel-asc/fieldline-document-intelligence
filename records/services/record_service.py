from django.db.models import Q

from documents.models import Document
from fieldline.logger import logger
from records.models import ExtractedRecord


SKIP_COLUMNS = {"document_id", "filename", "schema", "status", "line_items", "validation"}


class RecordService:
    def _owned(self, queryset, user):
        if getattr(user, "is_authenticated", False):
            return queryset.filter(created_by=user)
        return queryset.filter(created_by__isnull=True)

    def ingest(self, data, user=None):
        try:
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
            document_id = data.get("document_id")
            document = None
            if document_id:
                document = Document.objects.filter(pk=document_id).first()

            created_by = user if getattr(user, "is_authenticated", False) else None
            if created_by is None and document is not None:
                created_by = document.created_by

            queryset = ExtractedRecord.objects.all()
            record = None
            if document_id:
                record = queryset.filter(document_id=document_id).first()

            filename = data.get("filename") or (document.original_name if document else "document")
            schema_name = data.get("schema_name") or ""
            if not schema_name and document and document.schema:
                schema_name = document.schema.schema_name
            if not schema_name:
                schema_name = "Auto extract"

            fields = {
                "document": document,
                "original_name": filename,
                "schema_name": schema_name,
                "event": data.get("event") or "fieldline.document.extracted",
                "status": data.get("status") or (document.status if document else ""),
                "payload": payload,
                "webhook_status": (data.get("webhook_status") or "")[:80],
                "created_by": created_by,
            }
            if record:
                for key, value in fields.items():
                    setattr(record, key, value)
                record.save()
                return True, "Extracted row updated", record

            record = ExtractedRecord.objects.create(**fields)
            return True, "Extracted row saved", record
        except Exception as e:
            logger.error(f"Error ingesting extracted record: {e}")
            return False, f"Error ingesting extracted record: {e}", None

    def list_records(self, user=None, search=""):
        try:
            queryset = self._owned(
                ExtractedRecord.objects.select_related("document"),
                user,
            )
            if search:
                queryset = queryset.filter(
                    Q(original_name__icontains=search)
                    | Q(schema_name__icontains=search)
                    | Q(status__icontains=search)
                    | Q(payload__icontains=search)
                )
            return True, "Extracted rows fetched", queryset
        except Exception as e:
            logger.error(f"Error listing extracted records: {e}")
            return False, f"Error listing extracted records: {e}", None

    def column_keys(self, queryset):
        keys = []
        for record in queryset[:200]:
            data = record.payload if isinstance(record.payload, dict) else {}
            for key, value in data.items():
                if key in SKIP_COLUMNS or isinstance(value, (list, dict)):
                    continue
                if key not in keys:
                    keys.append(key)
        return keys
