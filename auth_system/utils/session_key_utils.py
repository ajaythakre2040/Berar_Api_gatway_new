from rest_framework.response import Response


def get_mis_auth_headers(request):
    session_key = request.headers.get("Session-Key")
    
    if not session_key:
        return None, Response(
            {"success": False, "error": "Authentication key is required."},
            status=403,
        )
    return {"Session-Key": session_key}, None
