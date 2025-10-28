
from rest_framework import serializers
from kyc_api_gateway.models import ProNameMatch

class ProNameMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProNameMatch
        fields = [
            "client_id",
            "request_id",
            "name_1",
            "name_2",
            "match_score",
            "match_status",
            "created_at",
        ]
