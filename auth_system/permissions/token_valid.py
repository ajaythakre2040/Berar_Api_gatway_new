from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework.exceptions import PermissionDenied
from auth_system.models.login_session import LoginSession


class IsTokenValid(BasePermission):
    """
    Custom permission to validate that:
    1. The token exists and is structurally valid.
    2. The token is not blacklisted.
    3. The token is associated with an active login session.
    """

    def has_permission(self, request, view):
        auth = JWTAuthentication()

        try:
            # 1. Extract token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise PermissionDenied(
                    "Authorization header is missing or improperly formatted."
                )

            raw_token = auth_header.split(" ")[1]

            # 2. Validate token structure
            validated_token = auth.get_validated_token(raw_token)

            # 3. Extract JTI (JWT ID) for blacklist checks
            jti = validated_token.get("jti")
            if not jti:
                raise PermissionDenied("Invalid token: missing token identifier (JTI).")

            # 4. Check if token is blacklisted
            if BlacklistedToken.objects.filter(token__jti=jti).exists():
                raise PermissionDenied("Your session has expired. Please log in again.")

            # 5. Check for active session
            if not LoginSession.objects.filter(
                token=raw_token, is_active=True
            ).exists():
                raise PermissionDenied(
                    "Your session has expired or is no longer valid."
                )

            return True

        except PermissionDenied:
            raise  # re-raise PermissionDenied without modifying message

        except Exception:
            raise PermissionDenied(
                "Authentication failed. Please provide a valid access token."
            )
