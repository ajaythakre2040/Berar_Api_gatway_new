from rest_framework import serializers
from kyc_api_gateway.models.client_management import ClientManagement
from django.contrib.auth.hashers import make_password

class ClientRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientManagement
        fields = [
            "company_name",
            "business_type",
            "registration_number",
            "tax_id",
            "website",
            "industry",
            "name",
            "email",
            "phone",
            "position",
            "risk_level",
            "compliance_level",
            "password",
        ]

    def create(self, validated_data):
        # password ko hash karna
        validated_data["password"] = make_password(validated_data["password"])
        validated_data["created_by"] = 1  # later you can use request.user.id
        return ClientManagement.objects.create(**validated_data)
