from pydantic import BaseModel, Field, field_validator
from typing import Literal


class CreateExportSchema(BaseModel):
    format: Literal["json", "csv"] = "json"
    source_range: Literal["today", "week", "all"] = "all"


class WebhookSchema(BaseModel):
    url: str = Field(..., description="Webhook URL")
    secret: str = ""

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        value = (value or "").strip()
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError("Enter a valid webhook URL")
        return value

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, value):
        return (value or "").strip()
