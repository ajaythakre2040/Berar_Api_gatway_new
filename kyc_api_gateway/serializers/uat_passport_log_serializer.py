from rest_framework import serializers
from kyc_api_gateway.models import UatPassportRequestLog

class UatPassportRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatPassportRequestLog
        fields = [
            "id",
            "passport_verification_id",  # FK reference
            "request_id",
            "file_number",
            "dob",
            "passport_number",
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
