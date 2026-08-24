from accounts.pipelines.base_pipeline import BasePipeline
from exports.services.export_service import ExportService
from fieldline.logger import logger


class ExportPipeline(BasePipeline):
    def __init__(self):
        self.export_service = ExportService()

    def process_item(self, data):
        return self.process_create(data, data.get("user"))

    def process_create(self, data, user=None):
        try:
            success, message, payload = self.export_service.create_export(data, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_create: {e}")
            return False, f"Error in process_create: {e}", None

    def process_list(self, user=None):
        try:
            success, message, payload = self.export_service.list_exports(user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_list: {e}")
            return False, f"Error in process_list: {e}", None

    def process_get(self, export_id, user=None):
        try:
            success, message, payload = self.export_service.get_export(export_id, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_get: {e}")
            return False, f"Error in process_get: {e}", None

    def process_sql(self, user=None, source_range="all"):
        try:
            success, message, payload = self.export_service.build_sql(
                user=user, source_range=source_range
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_sql: {e}")
            return False, f"Error in process_sql: {e}", None

    def process_get_webhook(self, user=None):
        try:
            success, message, payload = self.export_service.get_webhook(user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_get_webhook: {e}")
            return False, f"Error in process_get_webhook: {e}", None

    def process_save_webhook(self, data, user=None):
        try:
            success, message, payload = self.export_service.save_webhook(data, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_save_webhook: {e}")
            return False, f"Error in process_save_webhook: {e}", None

    def process_test_webhook(self, user=None):
        try:
            success, message, payload = self.export_service.test_webhook(user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_test_webhook: {e}")
            return False, f"Error in process_test_webhook: {e}", None
