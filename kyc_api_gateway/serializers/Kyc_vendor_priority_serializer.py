from rest_framework import serializers
from kyc_api_gateway.models import KycVendorPriority


class KycVendorPrioritySerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.vendor_name", read_only=True)
    service_name = serializers.CharField(source="my_service.name", read_only=True)
   
    class Meta:
        model = KycVendorPriority
      
        fields = [
            "id",
            "client",
            "client_name",
            "vendor",
            "vendor_name",
            "my_service",
            "service_name",
            "priority",
        ]

