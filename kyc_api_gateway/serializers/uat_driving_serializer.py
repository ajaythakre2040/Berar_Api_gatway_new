from rest_framework import serializers
from kyc_api_gateway.models import UatDrivingLicense


class UatDrivingLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatDrivingLicense
        fields = [
            "id",
            "client_id",
            "request_id",
            "dl_number",
            "name",
            "father_name",
            "dob",
            "issue_date",
            "valid_till",
            "address",
            "state",
            "rto_code",
            "blood_group",
            "photo",
            "signature",
            "is_verified",
            "vendor_name",
            "full_response",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
