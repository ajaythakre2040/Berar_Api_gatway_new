from rest_framework import serializers
from kyc_api_gateway.models.client_management import ClientManagement
from django.contrib.auth.hashers import check_password

class LoginSessionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            client = ClientManagement.objects.get(email=email, deleted_at__isnull=True)
        except ClientManagement.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        if not check_password(password, client.password):
            raise serializers.ValidationError("Invalid email or password")

        data["client"] = client
        return data
