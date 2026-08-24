import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from exports.models import WebhookDestination
from fieldline.logger import logger
from records.services.record_service import RecordService


class WebhookDispatchService:
    def document_payload(self, document, event):
        data = document.extracted_data if isinstance(document.extracted_data, dict) else {}
        return {
            "event": event,
            "document_id": document.id,
            "filename": document.original_name,
            "schema": document.schema.schema_name if document.schema else "",
            "status": document.status,
            "payload": data,
        }

    def post_json(self, url, payload):
        body = json.dumps(payload, default=str).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Fieldline-Webhook/1.0",
        }
        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=8) as response:
                return True, f"{response.status} OK"
        except HTTPError as e:
            return False, str(e.code)
        except URLError as e:
            logger.error(f"Webhook POST failed: {e}")
            return False, "Unreachable"
        except Exception as e:
            logger.error(f"Webhook POST failed: {e}")
            return False, str(e)

    def ingest_url(self):
        base = (getattr(settings, "SITE_URL", "") or "http://127.0.0.1:8000").rstrip("/")
        return f"{base}/app/records/api/ingest/"

    def dispatch_document(self, document, event="fieldline.document.extracted"):
        payload = self.document_payload(document, event)
        posted, status_label = self.post_json(self.ingest_url(), payload)
        if not posted:
            RecordService().ingest(
                {
                    "event": event,
                    "document_id": document.id,
                    "filename": document.original_name,
                    "schema_name": payload["schema"],
                    "status": document.status,
                    "payload": payload["payload"],
                    "webhook_status": status_label,
                },
                user=document.created_by,
            )
        user = document.created_by
        webhook = None
        queryset = WebhookDestination.objects.all()
        if getattr(user, "is_authenticated", False):
            webhook = queryset.filter(created_by=user).first()
        elif user is None:
            webhook = queryset.filter(created_by__isnull=True).first()
        if webhook and webhook.url:
            ok, dest_status = self.post_json(webhook.url, payload)
            webhook.last_status = (dest_status or "")[:80]
            webhook.save(update_fields=["last_status", "updated_at"])
            if not ok:
                logger.error(f"Destination webhook failed: {dest_status}")
        return posted, status_label
