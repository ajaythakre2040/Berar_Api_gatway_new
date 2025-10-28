from rest_framework import serializers
from kyc_api_gateway.models.client_management import ClientManagement


class ClientManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientManagement
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )
