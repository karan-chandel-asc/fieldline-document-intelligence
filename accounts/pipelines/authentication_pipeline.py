from accounts.pipelines.base_pipeline import BasePipeline
from accounts.services.authentication import AuthenticationService
from fieldline.logger import logger


class AuthenticationPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()

    def process_item(self, data):
        return self.process_registration(data)

    def process_registration(self, data):
        try:
            email_exists, message = self.authentication_service.check_email_already_exists(data["email"])
            if email_exists:
                return False, message, None

            user_registered, message = self.authentication_service.register_user(data)
            if not user_registered:
                return False, message, None

            return True, "Account created successfully. Please sign in.", None
        except Exception as e:
            logger.error(f"Error in process_registration: {e}")
            return False, f"Error in process_registration: {e}", None

    def process_login(self, data):
        try:
            credentials_valid, message, user = self.authentication_service.authenticate_user(
                data["email"], data["password"]
            )
            if not credentials_valid:
                return False, message, None
            return True, "Login successful", user
        except Exception as e:
            logger.error(f"Error in process_login: {e}")
            return False, f"Error in process_login: {e}", None

    def process_logout(self, request):
        try:
            success, message = self.authentication_service.logout_user(request)
            if not success:
                return False, message, None
            return True, message, None
        except Exception as e:
            logger.error(f"Error in process_logout: {e}")
            return False, f"Error in process_logout: {e}", None
