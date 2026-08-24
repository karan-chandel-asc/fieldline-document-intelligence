from accounts.pipelines.base_pipeline import BasePipeline
from fieldline.logger import logger
from records.services.record_service import RecordService


class RecordPipeline(BasePipeline):
    def __init__(self):
        self.record_service = RecordService()

    def process_item(self, data):
        return self.process_ingest(data)

    def process_ingest(self, data, user=None):
        try:
            success, message, payload = self.record_service.ingest(data, user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_ingest: {e}")
            return False, f"Error in process_ingest: {e}", None

    def process_list(self, user=None, search=""):
        try:
            success, message, payload = self.record_service.list_records(
                user=user, search=search
            )
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_list: {e}")
            return False, f"Error in process_list: {e}", None
