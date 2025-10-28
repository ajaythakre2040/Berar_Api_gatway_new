from rest_framework import serializers
from kyc_api_gateway.models import ProElectricityBill

class ProElectricityBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProElectricityBill
        fields = [
            "consumer_id",
            "service_provider",
            "full_name",
            "address",
            "mobile",
            "email",
            "operator_code",
            "district",
            "state",
            "reg_mobile_no",
            "bill_amount",
            "bill_due_date",
            "bill_status",
            "client_id",
        ]
