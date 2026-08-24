from django.shortcuts import render
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.pipelines.dashboard_pipeline import DashboardPipeline
from dashboard.serializers import DashboardOverviewSerializer
from fieldline.logger import logger
from fieldline.responses import error_response, success_response


def dashboard(request):
    return render(request, "dashboard/dashboard.html")


class DashboardOverviewApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    dashboard_pipeline = DashboardPipeline()

    def get(self, request):
        try:
            logger.info("Dashboard overview request received")
            success, message, payload = self.dashboard_pipeline.process_overview(
                user=request.user,
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(
                    message=message,
                    data=DashboardOverviewSerializer(payload).data,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error fetching dashboard overview: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
