from rest_framework import serializers
from kyc_api_gateway.models import UatElectricityBill

class UatElectricityBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatElectricityBill
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
