from django.http import FileResponse
from django.shortcuts import render
from pydantic import ValidationError
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from exports.pipelines.export_pipeline import ExportPipeline
from exports.schemas import CreateExportSchema, WebhookSchema
from exports.serializers import ExportBatchSerializer, WebhookDestinationSerializer
from fieldline.logger import logger
from fieldline.pagination import CustomPagination
from fieldline.responses import error_response, success_response
from fieldline.services.helper_services import HelperServices


def exports(request):
    return render(request, "exports/exports.html")


class ExportCreateApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    export_pipeline = ExportPipeline()
    helper_services = HelperServices()

    def post(self, request):
        try:
            logger.info("Export create request received")
            try:
                payload = CreateExportSchema(**self.helper_services.request_data(request))
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            success, message, batch = self.export_pipeline.process_create(
                payload.model_dump(),
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
                    data=ExportBatchSerializer(batch).data,
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error creating export: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportListApiView(GenericAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    serializer_class = ExportBatchSerializer
    pagination_class = CustomPagination
    export_pipeline = ExportPipeline()

    def get(self, request):
        try:
            logger.info("Export list request received")
            success, message, queryset = self.export_pipeline.process_list(user=request.user)
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            self.paginator.response_message = message
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing exports: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportDownloadApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    export_pipeline = ExportPipeline()

    def get(self, request, export_id):
        try:
            success, message, batch = self.export_pipeline.process_get(
                export_id, user=request.user
            )
            if not success or not batch or not batch.file:
                return Response(
                    error_response(message=message or "Export file missing"),
                    status=status.HTTP_404_NOT_FOUND,
                )
            return FileResponse(
                batch.file.open("rb"),
                as_attachment=True,
                filename=batch.filename,
            )
        except Exception as e:
            logger.error(f"Error downloading export: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportSqlApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    export_pipeline = ExportPipeline()

    def get(self, request):
        try:
            success, message, sql = self.export_pipeline.process_sql(
                user=request.user,
                source_range=request.GET.get("source_range") or "all",
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(message=message, data={"sql": sql}),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error generating export SQL: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WebhookApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    export_pipeline = ExportPipeline()
    helper_services = HelperServices()

    def get(self, request):
        try:
            success, message, webhook = self.export_pipeline.process_get_webhook(
                user=request.user
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(
                    message=message,
                    data=WebhookDestinationSerializer(webhook).data if webhook else None,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error fetching webhook: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            logger.info("Webhook save request received")
            try:
                payload = WebhookSchema(**self.helper_services.request_data(request))
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            success, message, webhook = self.export_pipeline.process_save_webhook(
                payload.model_dump(),
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
                    data=WebhookDestinationSerializer(webhook).data,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error saving webhook: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WebhookTestApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    export_pipeline = ExportPipeline()

    def post(self, request):
        try:
            logger.info("Webhook test request received")
            success, message, webhook = self.export_pipeline.process_test_webhook(
                user=request.user
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(
                    message=message,
                    data=WebhookDestinationSerializer(webhook).data,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error testing webhook: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
