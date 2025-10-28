from rest_framework import serializers
from auth_system.models.role_permission import RolePermission


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
