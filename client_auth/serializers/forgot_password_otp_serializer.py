from rest_framework import serializers
from client_auth.models import ForgotPasswordOtp

class ForgotPasswordOtpSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ForgotPasswordOtp
        fields = [
            "id",
            "client",
            "client_name",
            "token",
            "ip_address",
            "user_agent",
            "created_at",
            "expires_at",
            "is_expired",
        ]
        read_only_fields = ["id", "created_at", "is_expired"]

    def get_is_expired(self, obj):
        return "⏰ Expired" if obj.is_expired() else "✅ Active"
