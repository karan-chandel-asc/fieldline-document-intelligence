import json
import re

from django.conf import settings
from groq import Groq
from pypdf import PdfReader

from fieldline.logger import logger


class GroqExtractionService:
    def extract_text(self, file_path):
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            pages.append((page.extract_text() or "").strip())
        return "\n\n".join(part for part in pages if part).strip()

    def extract_fields(self, schema, document_text):
        if not settings.GROQ_API_KEY:
            return False, "Groq API key is missing", None
        if not document_text:
            return False, "No text could be read from this PDF", None

        fields = schema.schema_fields or []
        field_lines = []
        for field in fields:
            required = "required" if field.get("field_required") else "optional"
            field_lines.append(
                f"- {field.get('field_name')}: {field.get('field_type', 'string')} ({required})"
            )
        field_block = "\n".join(field_lines) or "- (no fields defined)"
        keys = [field.get("field_name") for field in fields if field.get("field_name")]
        prompt = (
            "Extract values from the document text using this extraction schema.\n"
            f"Schema name: {schema.schema_name}\n"
            f"Schema description: {schema.schema_description}\n"
            f"Fields:\n{field_block}\n\n"
            "Return a JSON object with exactly those field names as keys. "
            "Use null when a value is missing. Do not add extra keys.\n\n"
            f"Document text:\n{document_text[:12000]}"
        )

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You extract structured fields from documents. Reply with JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            raw = (completion.choices[0].message.content or "").strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return False, "Groq did not return a JSON object", None
            data = {key: parsed.get(key) for key in keys} if keys else parsed
            return True, "Fields extracted", data
        except Exception as e:
            logger.error(f"Groq extraction failed: {e}")
            return False, f"Groq extraction failed: {e}", None
