from rest_framework import serializers
from kyc_api_gateway.models.uat_pan_request_log import UatPanRequestLog
from kyc_api_gateway.models.client_management import ClientManagement

class UatPanRequestLogSerializer(serializers.ModelSerializer):

    client_name = serializers.SerializerMethodField()  # ✅ Add readable client name
    pan_details_id = serializers.IntegerField(source='pan_details.id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UatPanRequestLog
        fields = [
            'id',
            'pan_details_id',
            'pan_number',
            'user_name',
            'vendor',
            'endpoint',
            'status_code',
            'status',
            'request_payload',
            'response_payload',
            'error_message',
            'user_agent',
            'ip_address',
            'created_at',
            'created_by',
            'client_name',
        ]
        read_only_fields = ['created_at', 'created_by']


    def get_client_name(self, obj):
            try:
                client = ClientManagement.objects.filter(id=obj.created_by).first()
                return client.name if client else None
            except Exception:
                return None

