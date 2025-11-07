from rest_framework import serializers
from client_auth.models import LoginFailAttempt

class LoginFailAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginFailAttempt
        fields = [
            "id",
            "email",
            "ip",
            "agent_browser",
            "client_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["created_at"] = instance.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return rep
