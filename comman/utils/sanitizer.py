# import re


# def sanitize_input(value):
   
#     if not value:
#         return value

#     value = value.strip()
#     clean_value = re.sub(r"<.*?>", "", value)

#     if re.search(
#         r"(script|alert|onerror|onload|<|>|javascript:)", clean_value, re.IGNORECASE
#     ):
#         raise ValueError("Invalid characters detected in input.")

#     return clean_value

import re

def sanitize_input(value):
    # 1️⃣ Handle empty or None values
    if value is None or value == "":
        return value

    # 2️⃣ Handle string input
    if isinstance(value, str):
        value = value.strip()
        clean_value = re.sub(r"<.*?>", "", value)

        if re.search(r"(script|alert|onerror|onload|<|>|javascript:)", clean_value, re.IGNORECASE):
            raise ValueError("Invalid characters detected in input.")

        return clean_value

    # 3️⃣ Handle list input (e.g., multiple strings)
    elif isinstance(value, list):
        return [sanitize_input(v) for v in value]

    # 4️⃣ Handle dictionary input (optional)
    elif isinstance(value, dict):
        return {k: sanitize_input(v) for k, v in value.items()}

    # 5️⃣ Handle other types (int, bool, etc.)
    else:
        return value
