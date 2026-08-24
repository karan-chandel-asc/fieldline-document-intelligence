from pydantic import BaseModel, field_validator, model_validator


class UploadDocumentsSchema(BaseModel):
    schema_id: int | None = None

    @field_validator("schema_id", mode="before")
    @classmethod
    def validate_schema_id(cls, value):
        if value in (None, "", "0", 0):
            return None
        return int(value)


class ListDocumentsQuery(BaseModel):
    search: str = ""
    status: str = "all"
    schema_id: int | None = None
    received: str = ""

    @field_validator("search")
    @classmethod
    def validate_search(cls, value):
        return (value or "").strip()[:120]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        value = (value or "all").strip().lower()
        allowed = {
            "all",
            "queued",
            "processing",
            "needs_review",
            "review",
            "approved",
            "failed",
        }
        if value not in allowed:
            raise ValueError("Invalid status filter")
        return value

    @field_validator("schema_id", mode="before")
    @classmethod
    def validate_schema_filter(cls, value):
        if value in (None, "", "0", 0):
            return None
        return int(value)

    @field_validator("received")
    @classmethod
    def validate_received(cls, value):
        value = (value or "").strip().lower()
        allowed = {"", "any", "today", "7d", "last_7_days"}
        if value not in allowed:
            raise ValueError("Invalid received filter")
        if value in {"", "any"}:
            return ""
        return "7d" if value == "last_7_days" else value


class UpdateDocumentSchema(BaseModel):
    extracted_data: dict | None = None
    status: str | None = None
    error_message: str = ""
    schema_id: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value in (None, ""):
            return None
        value = str(value).strip().lower()
        if value not in {"needs_review", "approved", "failed"}:
            raise ValueError("Invalid status")
        return value

    @field_validator("error_message")
    @classmethod
    def validate_note(cls, value):
        return (value or "").strip()[:500]

    @field_validator("schema_id", mode="before")
    @classmethod
    def validate_schema_id(cls, value):
        if value in (None, "", "0", 0):
            return None
        return int(value)

    @model_validator(mode="after")
    def require_update(self):
        if self.extracted_data is None and self.status is None and self.schema_id is None:
            raise ValueError("Nothing to update")
        return self
