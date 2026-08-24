from pydantic import BaseModel, Field, field_validator
from typing import List, Literal


class SchemaField(BaseModel):
    field_name: str = Field(..., description="The name of the field")
    field_type: Literal[
        "string",
        "number",
        "boolean",
        "date",
        "time",
        "datetime",
        "array"
    ] = "string"
    field_required: bool = Field(
        False,
        description="Whether the field is required"
    )

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Field name cannot be empty")
        return value


class Schema(BaseModel):
    schema_name: str = Field(
        "Untitled",
        description="The name of the schema"
    )

    schema_description: str = Field(
        "No description provided",
        description="The description of the schema"
    )

    schema_fields: List[SchemaField] = Field(
        default_factory=list,
        description="The fields of the schema"
    )

    @field_validator("schema_name")
    @classmethod
    def validate_schema_name(cls, value):
        value = (value or "").strip()
        if not value:
            raise ValueError("Schema name cannot be empty")
        return value

    @field_validator("schema_description")
    @classmethod
    def validate_schema_description(cls, value):
        value = (value or "").strip()
        return value or "No description provided"

    def to_dict(self):
        return self.model_dump()