import jwt
from rest_framework import authentication, exceptions
from django.conf import settings
from client_auth.utils.token_utils import decode_client_token
from kyc_api_gateway.models.client_management import ClientManagement


class ClientJWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for client tokens (not using SimpleJWT).
    """

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        payload = decode_client_token(token)
        if "error" in payload:
            raise exceptions.AuthenticationFailed(payload["error"])

        client_id = payload.get("id")
        if not client_id:
            raise exceptions.AuthenticationFailed("Invalid token: missing client id")

        try:
            client = ClientManagement.objects.get(id=client_id)
        except ClientManagement.DoesNotExist:
            raise exceptions.AuthenticationFailed("Client not found")

        request.client = client
        return (client, None)
