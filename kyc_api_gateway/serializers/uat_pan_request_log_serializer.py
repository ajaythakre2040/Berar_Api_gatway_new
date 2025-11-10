from rest_framework import serializers
from kyc_api_gateway.models.uat_pan_request_log import UatPanRequestLog

class UatPanRequestLogSerializer(serializers.ModelSerializer):

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
        ]
        read_only_fields = ['created_at', 'created_by']
