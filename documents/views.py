import json

from django.shortcuts import render
from pydantic import ValidationError
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.pipelines.document_pipeline import DocumentPipeline
from documents.samples import SAMPLES, build_sql
from documents.schemas import ListDocumentsQuery, UploadDocumentsSchema
from documents.serializers import DocumentListSerializer, ExtractionJobSerializer
from documents.tasks import process_extraction_job
from fieldline.logger import logger
from fieldline.pagination import CustomPagination
from fieldline.responses import error_response, success_response
from fieldline.services.helper_services import HelperServices


def inbox(request):
    return render(request, "documents/inbox.html")


def review(request):
    key = request.GET.get("doc", "invoice")
    doc = SAMPLES.get(key, SAMPLES["invoice"])
    payload = json.dumps(doc["payload"], indent=2)
    sql = build_sql(doc["table"], doc["payload"])
    return render(
        request,
        "documents/review.html",
        {"doc": doc, "payload": payload, "sql": sql},
    )


def exceptions(request):
    return render(request, "documents/exceptions.html")


class DocumentUploadApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]
    document_pipeline = DocumentPipeline()
    helper_services = HelperServices()

    def post(self, request):
        try:
            logger.info("Document upload request received")
            try:
                payload = UploadDocumentsSchema(
                    schema_id=request.POST.get("schema_id") or 0
                )
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            success, message, job = self.document_pipeline.process_upload(
                request.FILES.getlist("files"),
                payload.schema_id,
                user=request.user,
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                async_result = process_extraction_job.delay(job.id)
                job.celery_task_id = async_result.id or ""
                job.save(update_fields=["celery_task_id"])
            except Exception as e:
                logger.error(f"Could not queue Celery job: {e}")
                return Response(
                    error_response(
                        message="Could not start the background worker. Start Redis and Celery, then try again."
                    ),
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            job = type(job).objects.prefetch_related("documents").select_related("schema").get(pk=job.id)
            return Response(
                success_response(
                    message=message,
                    data=ExtractionJobSerializer(job).data,
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error uploading documents: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExtractionJobApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    document_pipeline = DocumentPipeline()

    def get(self, request, job_id):
        try:
            success, message, job = self.document_pipeline.process_job_status(
                job_id,
                user=request.user,
            )
            if not success:
                return Response(
                    error_response(message=message),
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                success_response(
                    message=message,
                    data=ExtractionJobSerializer(job).data,
                ),
                status=status.HTTP_200_OK,
            )
            
        except Exception as e:
            logger.error(f"Error fetching extraction job: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentListApiView(GenericAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    serializer_class = DocumentListSerializer
    pagination_class = CustomPagination
    document_pipeline = DocumentPipeline()
    helper_services = HelperServices()

    def get(self, request):
        try:
            logger.info("Document list request received")
            try:
                query = ListDocumentsQuery(
                    search=request.GET.get("search") or "",
                    status=request.GET.get("status") or "all",
                    schema_id=request.GET.get("schema_id") or None,
                    received=request.GET.get("received") or "",
                )
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            success, message, queryset = self.document_pipeline.process_list(
                user=request.user,
                search=query.search,
                status=query.status,
                schema_id=query.schema_id,
                received=query.received,
            )
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
            logger.error(f"Error listing documents: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
