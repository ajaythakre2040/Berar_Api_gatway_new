from rest_framework import serializers
from kyc_api_gateway.models.kyc_my_services import KycMyServices


class KycMyServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = KycMyServices
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )
