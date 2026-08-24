import csv
import io
import json
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.utils import timezone

from documents.models import Document
from documents.samples import build_sql
from exports.models import ExportBatch, WebhookDestination
from fieldline.logger import logger


class ExportService:
    def _owned(self, queryset, user):
        if getattr(user, "is_authenticated", False):
            return queryset.filter(created_by=user)
        return queryset.filter(created_by__isnull=True)

    def _exportable_docs(self, user, source_range):
        queryset = self._owned(
            Document.objects.select_related("schema").filter(
                status__in=[Document.STATUS_NEEDS_REVIEW, Document.STATUS_APPROVED]
            ),
            user,
        ).order_by("-created_at")
        now = timezone.now()
        if source_range == ExportBatch.RANGE_TODAY:
            queryset = queryset.filter(created_at__date=now.date())
        elif source_range == ExportBatch.RANGE_WEEK:
            queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
        return queryset

    def _payload_rows(self, documents):
        rows = []
        for document in documents:
            row = {
                "document_id": document.id,
                "filename": document.original_name,
                "schema": document.schema.schema_name if document.schema else "",
                "status": document.status,
            }
            data = document.extracted_data if isinstance(document.extracted_data, dict) else {}
            row.update(data)
            rows.append(row)
        return rows

    def _csv_bytes(self, rows):
        keys = []
        for row in rows:
            for key in row.keys():
                if key not in keys and not isinstance(row.get(key), (list, dict)):
                    keys.append(key)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=keys or ["filename"], extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in keys})
        return buffer.getvalue().encode("utf-8")

    def create_export(self, data, user=None):
        try:
            fmt = data["format"]
            source_range = data["source_range"]
            documents = list(self._exportable_docs(user, source_range))
            if not documents:
                return False, "No extracted documents in that range", None

            rows = self._payload_rows(documents)
            stamp = timezone.now().strftime("%d%b").lower()
            if fmt == ExportBatch.FORMAT_CSV:
                content = self._csv_bytes(rows)
                filename = f"extracted-{stamp}.csv"
                content_type_name = filename
            else:
                content = json.dumps(rows, indent=2, default=str).encode("utf-8")
                filename = f"extracted-{stamp}.json"
                content_type_name = filename

            created_by = user if getattr(user, "is_authenticated", False) else None
            batch = ExportBatch(
                format=fmt,
                source_range=source_range,
                filename=filename,
                row_count=len(rows),
                status=ExportBatch.STATUS_READY,
                created_by=created_by,
            )
            batch.file.save(content_type_name, ContentFile(content), save=True)
            return True, "Export ready", batch
        except Exception as e:
            logger.error(f"Error creating export: {e}")
            return False, f"Error creating export: {e}", None

    def list_exports(self, user=None):
        try:
            queryset = self._owned(ExportBatch.objects.all(), user).order_by("-created_at")
            return True, "Exports fetched", queryset
        except Exception as e:
            logger.error(f"Error listing exports: {e}")
            return False, f"Error listing exports: {e}", None

    def get_export(self, export_id, user=None):
        try:
            queryset = self._owned(ExportBatch.objects.all(), user)
            batch = queryset.filter(pk=export_id).first()
            if not batch:
                return False, "Export not found", None
            return True, "Export fetched", batch
        except Exception as e:
            logger.error(f"Error fetching export: {e}")
            return False, f"Error fetching export: {e}", None

    def build_sql(self, user=None, source_range="all"):
        try:
            documents = list(self._exportable_docs(user, source_range)[:25])
            if not documents:
                return False, "No extracted documents to copy", None
            statements = []
            for document in documents:
                payload = {"filename": document.original_name}
                data = document.extracted_data if isinstance(document.extracted_data, dict) else {}
                payload.update(data)
                table = (document.schema.schema_name if document.schema else "extracted").lower().replace(" ", "_")
                statements.append(build_sql(table or "extracted", payload))
            return True, "SQL generated", "\n\n".join(statements)
        except Exception as e:
            logger.error(f"Error building export SQL: {e}")
            return False, f"Error building export SQL: {e}", None

    def get_webhook(self, user=None):
        try:
            queryset = self._owned(WebhookDestination.objects.all(), user)
            webhook = queryset.first()
            return True, "Webhook fetched", webhook
        except Exception as e:
            logger.error(f"Error fetching webhook: {e}")
            return False, f"Error fetching webhook: {e}", None

    def save_webhook(self, data, user=None):
        try:
            created_by = user if getattr(user, "is_authenticated", False) else None
            queryset = self._owned(WebhookDestination.objects.all(), user)
            webhook = queryset.first()
            if webhook:
                webhook.url = data["url"]
                webhook.secret = data.get("secret") or ""
                webhook.save(update_fields=["url", "secret", "updated_at"])
            else:
                webhook = WebhookDestination.objects.create(
                    url=data["url"],
                    secret=data.get("secret") or "",
                    created_by=created_by,
                )
            return True, "Webhook saved", webhook
        except Exception as e:
            logger.error(f"Error saving webhook: {e}")
            return False, f"Error saving webhook: {e}", None

    def test_webhook(self, user=None):
        try:
            success, message, webhook = self.get_webhook(user=user)
            if not success:
                return False, message, None
            if not webhook:
                return False, "Save a webhook URL first", None
            payload = json.dumps(
                {
                    "event": "fieldline.export.test",
                    "message": "Fieldline webhook test",
                }
            ).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if webhook.secret:
                headers["X-Fieldline-Secret"] = webhook.secret
            request = Request(webhook.url, data=payload, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=8) as response:
                    status_label = f"{response.status} OK"
            except HTTPError as e:
                status_label = str(e.code)
            except URLError as e:
                status_label = "Unreachable"
                logger.error(f"Webhook test failed: {e}")
            webhook.last_status = status_label
            webhook.last_tested_at = timezone.now()
            webhook.save(update_fields=["last_status", "last_tested_at", "updated_at"])
            return True, f"Webhook test → {status_label}", webhook
        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            return False, f"Error testing webhook: {e}", None
