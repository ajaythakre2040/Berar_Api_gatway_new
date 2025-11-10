from rest_framework import serializers
from kyc_api_gateway.models import UatDrivingLicenseRequestLog

class UatDrivingLicenseRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatDrivingLicenseRequestLog
        fields = [
            "id",
            "driving_license",
            "request_id",
            "dl_number",
            "name",
            "user",
            "vendor",
            "endpoint",
            "status_code",
            "status",
            "request_payload",
            "response_payload",
            "error_message",
            "created_at",
            "created_by",
        ]
