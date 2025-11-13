from rest_framework import serializers
from comman.utils.serielizer_input_sentizer import validate_and_sanitize
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

    def validate(self, attrs):
       
        attrs = validate_and_sanitize(attrs)  # Call the shared helper function
        return attrs