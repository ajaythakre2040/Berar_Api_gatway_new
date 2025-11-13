from rest_framework import serializers
from auth_system.models.role_permission import RolePermission
from comman.utils.serielizer_input_sentizer import validate_and_sanitize


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = [
            "role",
            "menu_id",
            "view",
            "add",
            "edit",
            "delete",
            "print",
            "export",
        ]
        extra_kwargs = {
            "role": {"read_only": True},
        }
        
    def validate(self, attrs):
       
        attrs = validate_and_sanitize(attrs)  # Call the shared helper function
        return attrs