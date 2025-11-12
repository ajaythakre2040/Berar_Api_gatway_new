

from rest_framework.exceptions import ValidationError

from comman.utils.sanitizer import sanitize_input
# from utils.sanitizer import sanitize_input


def validate_and_sanitize(attrs):
    """
    Validate and sanitize the input fields by checking for invalid characters.
    If invalid input is detected, raise a ValidationError.
    """
    for field_name, value in attrs.items():
        if value:  
            try:
                
                attrs[field_name] = sanitize_input(value)
            except ValueError as e:
                
                raise ValidationError(
                    {field_name: f"Invalid input for {field_name}: {str(e)}"}
                )
    return attrs
