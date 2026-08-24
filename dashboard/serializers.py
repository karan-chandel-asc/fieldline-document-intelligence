from rest_framework import serializers

from documents.serializers import DocumentListSerializer


class DashboardOverviewSerializer(serializers.Serializer):
    queued = serializers.IntegerField()
    needs_review = serializers.IntegerField()
    extracted_today = serializers.IntegerField()
    exceptions = serializers.IntegerField()
    pipeline_step = serializers.IntegerField()
    attention = DocumentListSerializer(many=True)
