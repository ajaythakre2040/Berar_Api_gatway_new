from rest_framework import serializers
from kyc_api_gateway.models.vendor_management import VendorManagement


class VendorManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorManagement
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )
