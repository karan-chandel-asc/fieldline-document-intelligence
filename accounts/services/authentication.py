from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.db.models import Q

from fieldline.logger import logger


class AuthenticationService:
    def check_email_already_exists(self, email):
        try:
            user = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
            if user:
                return True, "Email already exists"
            return False, "Email does not exist"
        except Exception as e:
            logger.error(f"Error checking email already exists: {e}")
            return False, f"Error checking email already exists: {e}"

    def register_user(self, data):
        try:
            email = data["email"]
            User.objects.create_user(
                username=email,
                email=email,
                password=data["password"],
                first_name=data.get("full_name", "")[:150],
            )
            return True, "User registered successfully"
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, f"Error registering user: {e}"

    def get_user_by_email(self, email):
        return User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()

    def authenticate_user(self, email, password):
        try:
            user = self.get_user_by_email(email)
            if not user or not user.check_password(password):
                return False, "Invalid email or password", None
            if not user.is_active:
                return False, "This account has been deactivated", None
            return True, "Credentials verified", user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, f"Error authenticating user: {e}", None

    def logout_user(self, request):
        try:
            auth_logout(request)
            return True, "Logged out successfully"
        except Exception as e:
            logger.error(f"Error logging out: {e}")
            return False, f"Error logging out: {e}"
