import re


def sanitize_input(value):
   
    if not value:
        return value

    value = value.strip()
    clean_value = re.sub(r"<.*?>", "", value)

    if re.search(
        r"(script|alert|onerror|onload|<|>|javascript:)", clean_value, re.IGNORECASE
    ):
        raise ValueError("Invalid characters detected in input.")

    return clean_value
