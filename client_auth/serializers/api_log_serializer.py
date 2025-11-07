from rest_framework import serializers
from client_auth.models import APILog


class APILogSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = APILog
        fields = [
            "id",
            "uniqid",
            "client",
            "client_name",
            "method",
            "endpoint",
            "request_data",
            "response_status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["created_at"] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return rep
