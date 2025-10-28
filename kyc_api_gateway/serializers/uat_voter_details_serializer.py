from rest_framework import serializers
from kyc_api_gateway.models import UatVoterDetail

class UatVoterDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatVoterDetail
        fields = [
            "voter_id",
            "name",
            "relation_name",
            "relation_type",
            "gender",
            "district",
            "state",
            "assembly_constituency",
            "assembly_constituency_number",
            "polling_station",
            "part_no",
            "part_name",
            "slno_in_part",
            "ps_lat_long",
            "name_v1",
            "name_v2",
            "name_v3",
            "rln_name_v1",
            "rln_name_v2",
            "rln_name_v3",
            "house_no",
            "last_update",
            "st_code",
            "parliamentary_name",
            "parliamentary_number",
            "vendor",
            "client_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]
