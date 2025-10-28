from rest_framework import serializers
from auth_system.models import AccountUnlockLog


class AccountUnlockLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountUnlockLog
        fields = [
            "id",
            "unlocked_by",
            "unlocked_user",
            "method",
            "timestamp",
            "ip_address",
            "user_agent",
            "success",
            "details",
        ]
        read_only_fields = ["id", "timestamp"]

    def to_representation(self, instance):
        # Get the default representation from the base class
        representation = super().to_representation(instance)

        # Format the 'timestamp' field to a human-readable string
        representation["timestamp"] = instance.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Convert the 'success' boolean field to a readable string (success/failure emoji)
        representation["success"] = "✅ Success" if instance.success else "❌ Failed"

        return representation
