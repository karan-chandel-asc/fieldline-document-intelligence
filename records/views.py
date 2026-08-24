from django.shortcuts import render
from pydantic import ValidationError
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from fieldline.logger import logger
from fieldline.pagination import CustomPagination
from fieldline.responses import error_response, success_response
from fieldline.services.helper_services import HelperServices
from records.pipelines.record_pipeline import RecordPipeline
from records.schemas import IngestExtractedSchema, ListRecordsQuery
from records.serializers import ExtractedRecordSerializer
from records.services.record_service import RecordService


def records(request):
    return render(request, "records/records.html")


class RecordIngestApiView(APIView):
    authentication_classes = []
    permission_classes = []
    record_pipeline = RecordPipeline()
    helper_services = HelperServices()

    def post(self, request):
        try:
            logger.info("Extracted record ingest received")
            try:
                payload = IngestExtractedSchema(**self.helper_services.request_data(request))
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            success, message, record = self.record_pipeline.process_ingest(
                payload.model_dump(),
                user=request.user if getattr(request.user, "is_authenticated", False) else None,
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                success_response(
                    message=message,
                    data=ExtractedRecordSerializer(record).data,
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error ingesting extracted record: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RecordListApiView(GenericAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    serializer_class = ExtractedRecordSerializer
    pagination_class = CustomPagination
    record_pipeline = RecordPipeline()
    helper_services = HelperServices()

    def get(self, request):
        try:
            logger.info("Extracted record list request received")
            try:
                query = ListRecordsQuery(search=request.GET.get("search") or "")
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            success, message, queryset = self.record_pipeline.process_list(
                user=request.user,
                search=query.search,
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            columns = RecordService().column_keys(queryset)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            self.paginator.response_message = message
            response = self.get_paginated_response(serializer.data)
            if isinstance(response.data, dict) and isinstance(response.data.get("data"), dict):
                response.data["data"]["columns"] = columns
            return response
        except Exception as e:
            logger.error(f"Error listing extracted records: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
