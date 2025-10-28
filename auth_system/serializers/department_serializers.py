from rest_framework import serializers
from auth_system.models.department import Department

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )
