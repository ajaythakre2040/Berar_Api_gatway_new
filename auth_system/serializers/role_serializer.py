from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.utils.text import slugify
import re

from auth_system.models.role import Role
from auth_system.models.role_permission import RolePermission
from auth_system.serializers.role_permission_serializer import RolePermissionSerializer
from django.contrib.auth.models import Permission

from comman.utils.serielizer_input_sentizer import validate_and_sanitize  

class RoleWithOutPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )


class RoleSerializer(serializers.ModelSerializer):
    permission = RolePermissionSerializer(many=True, write_only=True)
    permissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "role_name",
            "level",
            "type",
            "description",
            "role_code",
            "permission",
            "permissions",
        ]
        read_only_fields = ["role_code"]

    def get_permissions(self, obj):
        active_permissions = obj.permissions.filter(deleted_at__isnull=True)
        return RolePermissionSerializer(active_permissions, many=True).data
    def validate(self, attrs):
       
        attrs = validate_and_sanitize(attrs)  
        return attrs
    def validate_permission(self, value):
        seen = set()
        for item in value:
            menu_id = item.get("menu_id")
            if menu_id in seen:
                raise serializers.ValidationError(
                    f"Duplicate permission found for menu_id = {menu_id}"
                )
            seen.add(menu_id)
        return value

    def create(self, validated_data):
        permissions_data = validated_data.pop("permission", [])
        request = self.context.get("request")
        user_id = getattr(request.user, "id", None) if request else None

        base_name = (
            slugify(validated_data.get("role_name", "")).upper().replace("_", "")
        )

        existing_codes = Role.objects.filter(
            role_code__startswith=base_name
        ).values_list("role_code", flat=True)

        max_number = 0
        pattern = re.compile(rf"{base_name}(\d{{4}})$")

        for code in existing_codes:
            match = pattern.match(code)
            if match:
                number = int(match.group(1))
                if number > max_number:
                    max_number = number

        new_number = max_number + 1
        padded_number = str(new_number).zfill(4)

        role_code = f"{base_name}{padded_number}"

        role = Role.objects.create(
            **validated_data,
            role_code=role_code,
            created_by=user_id,
        )

        RolePermission.objects.bulk_create(
            [
                RolePermission(role=role, created_by=user_id, **perm)
                for perm in permissions_data
            ]
        )

        return role

    def update(self, instance, validated_data):
        permissions_data = validated_data.pop("permission", None)
        request = self.context.get("request")
        user_id = getattr(request.user, "id", None) if request else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.updated_by = user_id
        instance.updated_at = timezone.now()
        instance.save()

        if permissions_data:
            with transaction.atomic():
                menu_ids = [
                    perm.get("menu_id")
                    for perm in permissions_data
                    if perm.get("menu_id") is not None
                ]

                RolePermission.objects.filter(
                    role=instance, menu_id__in=menu_ids, deleted_at__isnull=True
                ).update(deleted_at=timezone.now(), deleted_by=user_id)

                RolePermission.objects.bulk_create(
                    [
                        RolePermission(role=instance, created_by=user_id, **perm)
                        for perm in permissions_data
                        if perm.get("menu_id") is not None
                    ]
                )

        return instance
