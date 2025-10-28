from rest_framework import serializers
from kyc_api_gateway.models.kyc_client_services_management import KycClientServicesManagement
from kyc_api_gateway.models.client_management import ClientManagement
from kyc_api_gateway.models.kyc_my_services import KycMyServices


class KycClientServicesManagementSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    service_name = serializers.CharField(source="myservice.name", read_only=True)

    class Meta:
        model = KycClientServicesManagement
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )
