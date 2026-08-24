from accounts.pipelines.base_pipeline import BasePipeline
from fieldline.logger import logger
from schemas.services.schema_service import SchemaService


class SchemaPipeline(BasePipeline):
    def __init__(self):
        self.schema_service = SchemaService()

    def process_item(self, data):
        return self.process_save(data)

    def process_save(self, data, user=None):
        try:
            success, message, payload = self.schema_service.create_schema(data, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_save: {e}")
            return False, f"Error in process_save: {e}", None

    def process_list(self, user=None):
        try:
            success, message, payload = self.schema_service.list_schemas(user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_list: {e}")
            return False, f"Error in process_list: {e}", None

    def process_delete(self, schema_id, user=None):
        try:
            success, message, payload = self.schema_service.delete_schema(
                schema_id, user=user
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_delete: {e}")
            return False, f"Error in process_delete: {e}", None
