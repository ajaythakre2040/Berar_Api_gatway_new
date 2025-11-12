from rest_framework import serializers
from auth_system.models.department import Department
from comman.utils.serielizer_input_sentizer import validate_and_sanitize

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
    def validate(self, attrs):
       
        attrs = validate_and_sanitize(attrs)  # Call the shared helper function
        return attrs