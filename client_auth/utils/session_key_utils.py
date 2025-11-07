from rest_framework.response import Response
from rest_framework import status


def get_client_auth_headers(request):
    """
    Extract authentication headers from request.
    Supports both Session-Key (custom) and JWT Bearer Token.
    Returns (headers_dict, error_response)
    """

    session_key = request.headers.get("Session-Key")
    auth_header = request.headers.get("Authorization")

    if session_key:
        return {"Session-Key": session_key}, None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        return {"Authorization": f"Bearer {token}"}, None

    return None, Response(
        {
            "success": False,
            "error": "Authentication credentials were not provided.",
        },
        status=status.HTTP_403_FORBIDDEN,
    )
