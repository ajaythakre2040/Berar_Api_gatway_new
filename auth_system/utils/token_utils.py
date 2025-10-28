from typing import Optional, Union
from datetime import datetime
from django.utils.timezone import make_aware
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


def generate_tokens_for_user(user: AbstractBaseUser) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)

    refresh["email"] = user.email
    refresh["full_name"] = user.full_name
    refresh["mobile_number"] = user.mobile_number

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def blacklist_token(
    token_str: str, token_type: str, user: Optional[AbstractBaseUser] = None
) -> None:
    token_cls: Union[type[RefreshToken], type[AccessToken]] = (
        RefreshToken if token_type == "refresh" else AccessToken
    )
    token = token_cls(token_str)

    expires_at = make_aware(datetime.fromtimestamp(token["exp"]))
    outstanding_token, _ = OutstandingToken.objects.get_or_create(
        jti=token["jti"],
        defaults={
            "user": user,
            "token": str(token),
            "created_at": timezone.now(),
            "expires_at": expires_at,
        },
    )

    BlacklistedToken.objects.get_or_create(token=outstanding_token)
