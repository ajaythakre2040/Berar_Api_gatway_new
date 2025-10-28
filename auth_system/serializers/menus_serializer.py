from rest_framework import serializers

from auth_system.models.menus import Menu


class MenuSerializer(serializers.ModelSerializer):

    class Meta:
        model = Menu
        fields = [
            "id",
            "menu_name",
            "menu_code",
            "sort_id",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "deleted_by",
            "deleted_at",
        ]
        read_only_fields = (
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "deleted_by",
            "deleted_at",
        )

    def validate_sort_id(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Menu sort id  cannot be negative.")
        return value
