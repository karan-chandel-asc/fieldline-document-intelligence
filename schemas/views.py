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
from schemas.pipelines.schema_pipeline import SchemaPipeline
from schemas.schemas import Schema as SchemaPayload
from schemas.serializers import SchemaDeleteSerializer, SchemaListSerializer, SchemaSerializer


def schemas(request):
    return render(request, "schemas/schemas.html")


class SchemaSaveApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    schema_pipeline = SchemaPipeline()
    helper_services = HelperServices()

    def post(self, request):
        try:
            logger.info("Schema save request received")
            try:
                schema = SchemaPayload(**self.helper_services.request_data(request))
            except ValidationError as e:
                message = self.helper_services.schema_error(e)
                return Response(
                    error_response(message=message),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            success, message, payload = self.schema_pipeline.process_save(
                schema.to_dict(),
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
                    data=SchemaSerializer(payload).data,
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error saving schema: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SchemaListApiView(GenericAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    serializer_class = SchemaListSerializer
    pagination_class = CustomPagination
    schema_pipeline = SchemaPipeline()

    def get(self, request):
        try:
            logger.info("Schema list request received")
            success, message, queryset = self.schema_pipeline.process_list(
                user=request.user,
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
            logger.error(f"Error listing schemas: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SchemaDeleteApiView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    schema_pipeline = SchemaPipeline()

    def delete(self, request, schema_id):
        try:
            logger.info("Schema delete request received")
            success, message, payload = self.schema_pipeline.process_delete(
                schema_id,
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
                    data=SchemaDeleteSerializer(payload).data,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error deleting schema: {e}")
            return Response(
                error_response(message=str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

