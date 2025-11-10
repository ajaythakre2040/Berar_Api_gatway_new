from rest_framework import serializers
from kyc_api_gateway.models import UatAddressMatchRequestLog

class UatAddressMatchRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatAddressMatchRequestLog
        fields = [
            "id",
            "address_match",
            "address1",
            "address2",
            "user",
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
