from rest_framework import serializers
from client_auth.models import AccountUnlockLog


class AccountUnlockLogSerializer(serializers.ModelSerializer):
    unlocked_by_name = serializers.CharField(source="unlocked_by.company_name", read_only=True)
    unlocked_client_name = serializers.CharField(source="unlocked_client.company_name", read_only=True)

    class Meta:
        model = AccountUnlockLog
        fields = [
            "id",
            "unlocked_by",
            "unlocked_by_name",
            "unlocked_client",
            "unlocked_client_name",
            "method",
            "timestamp",
            "ip_address",
            "user_agent",
            "success",
            "details",
        ]
        read_only_fields = ["id", "timestamp"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["timestamp"] = instance.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return rep
