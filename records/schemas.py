from pydantic import BaseModel, Field, field_validator


class IngestExtractedSchema(BaseModel):
    event: str = "fieldline.document.extracted"
    document_id: int | None = None
    filename: str = ""
    schema_name: str = Field(default="", alias="schema")
    status: str = ""
    payload: dict = Field(default_factory=dict)
    webhook_status: str = ""

    model_config = {"populate_by_name": True}

    @field_validator("event")
    @classmethod
    def validate_event(cls, value):
        return (value or "fieldline.document.extracted").strip()[:80]

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value):
        return (value or "").strip()[:255]

    @field_validator("schema_name", mode="before")
    @classmethod
    def validate_schema_name(cls, value):
        return (value or "").strip()[:160]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        return (value or "").strip()[:40]

    @field_validator("payload", mode="before")
    @classmethod
    def validate_payload(cls, value):
        return value if isinstance(value, dict) else {}

    @field_validator("document_id", mode="before")
    @classmethod
    def validate_document_id(cls, value):
        if value in (None, "", 0, "0"):
            return None
        return int(value)


class ListRecordsQuery(BaseModel):
    search: str = ""

    @field_validator("search")
    @classmethod
    def validate_search(cls, value):
        return (value or "").strip()[:120]
