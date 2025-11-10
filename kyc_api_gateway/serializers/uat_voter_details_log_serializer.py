from rest_framework import serializers
from kyc_api_gateway.models import UatVoterRequestLog

class UatVoterRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatVoterRequestLog
        fields = [
            "id",
            "voter_detail_id",    
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
