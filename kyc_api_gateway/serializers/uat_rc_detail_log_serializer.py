from rest_framework import serializers
from kyc_api_gateway.models import UatRcRequestLog

class UatRcRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatRcRequestLog
        fields = [
            "id",
            "rc_details_id",        # ForeignKey reference
            "rc_number",
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
