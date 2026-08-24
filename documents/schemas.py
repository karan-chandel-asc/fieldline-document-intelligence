from pydantic import BaseModel, Field, field_validator


class UploadDocumentsSchema(BaseModel):
    schema_id: int = Field(..., description="Saved extraction schema id")

    @field_validator("schema_id")
    @classmethod
    def validate_schema_id(cls, value):
        if int(value) < 1:
            raise ValueError("Select a schema")
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
        allowed = {"all", "queued", "processing", "needs_review", "review", "failed"}
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
