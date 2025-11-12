import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.timezone import make_aware
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from client_auth.models.blacklisted_token import BlacklistedToken

SECRET_KEY = settings.SECRET_KEY


def generate_tokens_for_client(client):
    """
    Generate access and refresh tokens for the given client, with respective expiry durations.
    """

    access_lifetime = getattr(settings, "SIMPLE_JWT", {}).get(
        "ACCESS_TOKEN_LIFETIME", timedelta(hours=1)
    )
    refresh_lifetime = getattr(settings, "SIMPLE_JWT", {}).get(
        "REFRESH_TOKEN_LIFETIME", timedelta(days=1)
    )

    print(f"Access Token Expiry: {access_lifetime}")
    print(f"Refresh Token Expiry: {refresh_lifetime}")

    access_expiry = make_aware(datetime.utcnow()) + access_lifetime
    refresh_expiry = make_aware(datetime.utcnow()) + refresh_lifetime

    access_payload = {
        "id": client.id,
        "client_id": client.id,
        "email": client.email,
        "company_name": client.company_name,
        "exp": access_expiry,
        "type": "access",
    }

    refresh_payload = {
        "id": client.id,
        "client_id": client.id,
        "email": client.email,
        "exp": refresh_expiry,
        "type": "refresh",
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm="HS256")

    return {
        "access": access_token,
        "refresh": refresh_token,
    }


def decode_client_token(token):
    """
    Decode the client token and verify its expiration.
    """
    try:

        payload = jwt.decode(
            token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": True}
        )

        exp_timestamp = payload.get("exp")
        if exp_timestamp and make_aware(datetime.utcnow()).timestamp() > exp_timestamp:
            return {"error": "Token has expired"}

        return payload

    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


def blacklist_token(token, token_type, client):
    """
    Save the token to the blacklist to prevent future use.
    """

    if not BlacklistedToken.objects.filter(token=token).exists():
        BlacklistedToken.objects.create(
            client=client,
            token=token,
            token_type=token_type,
            blacklisted_at=make_aware(datetime.utcnow()),
        )


class ClientPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator for password reset.
    """

    def _make_hash_value(self, client, timestamp):

        return (
            str(client.pk) + str(client.email) + str(client.password) + str(timestamp)
        )


client_token_generator = ClientPasswordResetTokenGenerator()
