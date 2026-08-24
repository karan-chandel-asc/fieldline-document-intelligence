from rest_framework import serializers

from schemas.models import Schema


class SchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ("id", "schema_name", "schema_description", "schema_fields")
        read_only_fields = ("id",)


class SchemaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ("id", "schema_name", "schema_description", "schema_fields")
        read_only_fields = fields


class SchemaDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schema
        fields = ("id", "schema_name")
        read_only_fields = fields
