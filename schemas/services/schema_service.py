from fieldline.logger import logger
from schemas.models import Schema


class SchemaService:
    def create_schema(self, data, user=None):
        try:
            already_exists = Schema.objects.filter(schema_name=data["schema_name"]).exists()
            if already_exists:
                return False, "A schema with this name already exists", None

            created_by = user if getattr(user, "is_authenticated", False) else None
            schema = Schema.objects.create(
                schema_name=data["schema_name"],
                schema_description=data["schema_description"],
                schema_fields=data["schema_fields"],
                created_by=created_by,
            )
            return True, "Schema saved", schema
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            return False, f"Error creating schema: {e}", None

    def list_schemas(self, user=None):
        try:
            queryset = Schema.objects.all().order_by("-created_at")
            if getattr(user, "is_authenticated", False):
                queryset = queryset.filter(created_by=user)
            else:
                queryset = queryset.filter(created_by__isnull=True)
            return True, "Schemas fetched", queryset
        except Exception as e:
            logger.error(f"Error listing schemas: {e}")
            return False, f"Error listing schemas: {e}", None

    def delete_schema(self, schema_id, user=None):
        try:
            queryset = Schema.objects.filter(pk=schema_id)
            if getattr(user, "is_authenticated", False):
                queryset = queryset.filter(created_by=user)
            else:
                queryset = queryset.filter(created_by__isnull=True)
            schema = queryset.first()
            if not schema:
                return False, "Schema not found", None
            schema_id_value = schema.pk
            schema.delete()
            schema.pk = schema_id_value
            return True, "Schema deleted", schema
        except Exception as e:
            logger.error(f"Error deleting schema: {e}")
            return False, f"Error deleting schema: {e}", None
