from rest_framework import serializers
from comman.utils.serielizer_input_sentizer import validate_and_sanitize
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

    def validate(self, attrs):
        
        attrs = validate_and_sanitize(attrs)  # Call the shared helper function
        return attrs