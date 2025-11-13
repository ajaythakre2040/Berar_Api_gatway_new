import re


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


@staticmethod
def sanitize_input(value):
    if not value:
        return value

    value = value.strip()

    if re.search(r"<[^>]+>", value):
        raise ValueError("HTML tags are not allowed in input.")

    if re.search(r"(script|alert|onerror|onload|javascript:)", value, re.IGNORECASE):
        raise ValueError("Invalid characters or script patterns detected in input.")

    return value
