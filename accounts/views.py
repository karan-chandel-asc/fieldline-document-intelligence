from django.contrib.auth import login as auth_login
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from pydantic import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.pipelines.authentication_pipeline import AuthenticationPipeline
from accounts.schemas import LoginSchema, SignupSchema
from fieldline.logger import logger
from fieldline.responses import error_response, success_response
from fieldline.services.helper_services import HelperServices

@method_decorator(ensure_csrf_cookie, name="dispatch")
class SignupPage(TemplateView):
    template_name = "accounts/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class SignupApiView(APIView):
    authentication_classes = []
    permission_classes = []
    authentication_pipeline = AuthenticationPipeline()
    helper_services = HelperServices()

    def post(self, request):
        try:
            logger.info("Signup request received")
            try:
                signup_schema = SignupSchema(**self.helper_services.request_data(request))
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            reg_success, message, new_user = self.authentication_pipeline.process_registration(
                signup_schema.model_dump()
            )
            if not reg_success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(
                    message="Account created successfully. Please sign in."
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error signing up: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginPage(TemplateView):
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(HelperServices.safe_next(request))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = HelperServices.safe_next(self.request)
        context["created"] = self.request.GET.get("created") == "1"
        return context


class LoginApiView(APIView):
    authentication_classes = []
    permission_classes = []
    authentication_pipeline = AuthenticationPipeline()
    helper_services = HelperServices()

    def post(self, request):
        try:
            logger.info("Login request received")
            data = self.helper_services.request_data(request)
            try:
                login_schema = LoginSchema(**data)
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            success, message, user = self.authentication_pipeline.process_login(
                login_schema.model_dump()
            )
            if not success or user is None:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            auth_login(request, user)
            return Response(
                success_response(
                    message=message,
                    data={"redirect": HelperServices.safe_next(request)},
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class LogoutPage(View):
    def get(self, request):
        AuthenticationPipeline().process_logout(request)
        return redirect("login")


class LogoutApiView(APIView):
    authentication_classes = []
    permission_classes = []
    authentication_pipeline = AuthenticationPipeline()

    def post(self, request):
        try:
            logger.info("Logout request received")
            success, message, _payload = self.authentication_pipeline.process_logout(request)
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(
                    message=message,
                    data={"redirect": reverse("login")},
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error logging out: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
