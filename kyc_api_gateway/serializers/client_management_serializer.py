from rest_framework import serializers
from comman.utils.serielizer_input_sentizer import validate_and_sanitize
from kyc_api_gateway.models.client_management import ClientManagement
from kyc_api_gateway.utils.key_generator import generate_secure_token


# class ClientManagementSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = ClientManagement
#         exclude = (
#             "created_by",
#             "updated_by",
#             "deleted_by",
#             "created_at",
#             "updated_at",
#             "deleted_at",
#         )

#     def validate(self, attrs):
        
#         # sanitize inputs
#         attrs = validate_and_sanitize(attrs)

#         # Auto-generate UAT key (without prefix)
#         if not attrs.get("uat_key"):
#             attrs["uat_key"] = generate_secure_token()

#         # Auto-generate Production key (without prefix)
#         if not attrs.get("production_key"):
#             attrs["production_key"] = generate_secure_token()

#         return attrs


class ClientManagementSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClientManagement
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )

    def validate(self, attrs):
        # sanitize inputs
        attrs = validate_and_sanitize(attrs)

        # ✔ ONLY generate keys when creating a new client
        if self.instance is None:
            if not attrs.get("uat_key"):
                attrs["uat_key"] = generate_secure_token()

            if not attrs.get("production_key"):
                attrs["production_key"] = generate_secure_token()

        # ✔ On UPDATE → use existing values, do NOT generate new
        return attrs
