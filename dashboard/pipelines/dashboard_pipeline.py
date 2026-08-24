from accounts.pipelines.base_pipeline import BasePipeline
from dashboard.services.overview_service import DashboardService
from fieldline.logger import logger


class DashboardPipeline(BasePipeline):
    def __init__(self):
        self.dashboard_service = DashboardService()

    def process_item(self, data):
        return self.process_overview(data.get("user"))

    def process_overview(self, user=None):
        try:
            success, message, payload = self.dashboard_service.get_overview(user=user)
            if not success:
                return False, message, None
            return True, message, payload
        except Exception as e:
            logger.error(f"Error in process_overview: {e}")
            return False, f"Error in process_overview: {e}", None
