from rest_framework import serializers
from client_auth.models import PasswordResetLog

class PasswordResetLogSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = PasswordResetLog
        fields = [
            "id",
            "client",
            "client_name",
            "email",
            "ip_address",
            "user_agent",
            "action",
            "timestamp",
            "successful",
            "details",
        ]
        read_only_fields = ["id", "timestamp"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["timestamp"] = instance.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        rep["successful"] = "✅ Success" if instance.successful else "❌ Failed"
        return rep
