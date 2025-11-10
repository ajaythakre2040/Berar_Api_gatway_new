from rest_framework import serializers
from kyc_api_gateway.models import UatNameMatchRequestLog, ClientManagement

class UatNameMatchRequestLogSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()  # ✅ Add readable client name

    class Meta:
        model = UatNameMatchRequestLog
        fields = [
            "id",
            "name_match_id",
            "request_id",
            "name_1",
            "name_2",
            "vendor",
            "endpoint",
            "status_code",
            "status",
            "request_payload",
            "response_payload",
            "error_message",
            "user_agent",
            "ip_address",
            "created_at",
            "created_by",
            "client_name", 
        ]
        read_only_fields = ["id", "created_at"]

    def get_client_name(self, obj):
        try:
            client = ClientManagement.objects.filter(id=obj.created_by).first()
            return client.name if client else None
        except Exception:
            return None
