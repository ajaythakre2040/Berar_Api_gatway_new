from rest_framework import serializers
from auth_system.models.login_session import LoginSession

class LoginSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginSession
        fields = [
            "id",
            "user",
            "token",
            "is_active",
            "created_at",
            "login_at",
            "logout_at",
            "expiry_at",
            "ip_address",
            "agent_browser",
            "request_headers",
        ]
        read_only_fields = ["id", "created_at", "login_at"]
