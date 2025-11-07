from rest_framework import serializers
from kyc_api_gateway.models import UatAddressMatch


class UatAddressMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatAddressMatch
        fields = [
            "id",
            "client_id",
            "request_id",
            "score",
            "match",
            "success",
            "status_code",
            "message",
            "house",
            "locality",
            "street",
            "district",
            "city",
            "state",
            "pincode",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]

    def to_representation(self, instance):
       
        data = super().to_representation(instance)

        vendor_response = getattr(instance, "vendor_response", None)
        if vendor_response and isinstance(vendor_response, dict):
            result = vendor_response.get("result", {})
            address1 = result.get("address1", {})

            data.update({
                "score": result.get("score"),
                "match": result.get("match"),
                "status_code": vendor_response.get("statusCode"),
                "address_locality": address1.get("locality"),
                "address_district": address1.get("district"),
                "address_state": address1.get("state"),
                "address_pincode": address1.get("pin"),
            })

        return data
