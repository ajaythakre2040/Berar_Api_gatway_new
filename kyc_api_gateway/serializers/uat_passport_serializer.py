

from rest_framework import serializers
from kyc_api_gateway.models import UatPassportDetails

class UatPassportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatPassportDetails
        fields = [
            "client_id",
            "request_id",
            "passport_number",
            "file_number",
            "full_name",
            "surname",
            "dob",
            "date_of_issue",
            "date_of_application",
            "application_type",
            "status_text",
            "created_at",
            "updated_at",
        ]
