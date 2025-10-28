
from rest_framework import serializers
from kyc_api_gateway.models import UatNameMatch

class UatNameMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatNameMatch
        fields = [
            "client_id",
            "request_id",
            "name_1",
            "name_2",
            "match_score",
            "match_status",
            "created_at",
        ]
