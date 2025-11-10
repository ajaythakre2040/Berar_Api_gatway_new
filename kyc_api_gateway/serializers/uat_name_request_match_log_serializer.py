from rest_framework import serializers
from kyc_api_gateway.models import UatNameMatchRequestLog

class UatNameMatchRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatNameMatchRequestLog
        fields = [
            "id",
            "name_match_id",
            "request_id",
            "name_1",
            "name_2",
            "vendor",
            "endpoint",
            "status_code",
            "status",
            "request_payload",
            "response_payload",
            "error_message",
            "user_agent",
            "ip_address",
            "created_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at"]
