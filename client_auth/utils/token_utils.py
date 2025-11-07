import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.timezone import make_aware
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from client_auth.models.blacklisted_token import BlacklistedToken

SECRET_KEY = settings.SECRET_KEY

def generate_tokens_for_client(client):
    access_lifetime = getattr(settings, "ACCESS_TOKEN_LIFETIME", timedelta(hours=1))
    refresh_lifetime = getattr(settings, "REFRESH_TOKEN_LIFETIME", timedelta(days=1))

    access_payload = {
        "id": client.id,  # Add this line
        "client_id": client.id,
        "email": client.email,
        "company_name": client.company_name,
        "exp": datetime.utcnow() + access_lifetime,
        "type": "access",
    }

    refresh_payload = {
        "id": client.id,  # Add this line
        "client_id": client.id,
        "email": client.email,
        "exp": datetime.utcnow() + refresh_lifetime,
        "type": "refresh",
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm="HS256")

    return {
        "access": access_token,
        "refresh": refresh_token,
    }

def decode_client_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
            return {"error": "Token has expired"}
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
    
def blacklist_token(token, token_type, client):
    """
    Save token to blacklist to prevent future use
    """
    if not BlacklistedToken.objects.filter(token=token).exists():
        BlacklistedToken.objects.create(
            client=client,
            token=token,
            token_type=token_type
        )



class ClientPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, client, timestamp):
        return str(client.pk) + str(client.email) + str(client.password) + str(timestamp)

client_token_generator = ClientPasswordResetTokenGenerator()