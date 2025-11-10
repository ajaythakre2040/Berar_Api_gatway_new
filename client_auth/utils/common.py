from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import CommonPasswordValidator
import re


def token_expiry_time():

    access_lifetime = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME", timedelta(minutes=30))
    return timezone.now() + access_lifetime


def refresh_token_expiry_time():

    refresh_lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME", timedelta(days=7))
    return timezone.now() + refresh_lifetime


def validate_password(password):
  
    errors = []

    # ✅ Basic rules
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character.")
    if not password[0].isupper():
        errors.append("Password must start with a capital letter.")

    try:
        CommonPasswordValidator().validate(password)
    except ValidationError as e:
        errors.extend(e.messages)

    if errors:
        raise ValidationError(errors)


def get_client_ip_and_agent(request):

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")

    agent = request.META.get("HTTP_USER_AGENT", "Unknown")
    return ip, agent
