from rest_framework import serializers
from kyc_api_gateway.models import UatBillRequestLog

class UatBillRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatBillRequestLog
        fields = [
            "id",
            "bill_details",
            "customer_id",
            "operator_code",
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
