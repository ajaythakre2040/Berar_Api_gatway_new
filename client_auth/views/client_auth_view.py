from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from auth_system.permissions.token_valid import IsTokenValid
from client_auth.models.blacklisted_token import BlacklistedToken
from client_auth.models.login_otp_verification import LoginOtpVerification
from client_auth.permissions.authentication import ClientJWTAuthentication
from client_auth.permissions.permissions import IsClientAuthenticated
from client_auth.utils.otp_utils import send_login_otp
from constant import MAX_LOGIN_ATTEMPTS, DeliveryStatus
from kyc_api_gateway.models.client_management import ClientManagement
from client_auth.models.login_session import LoginSession
from client_auth.models.login_fail_attempt import LoginFailAttempt
from client_auth.models.forgot_password import ForgotPassword
from client_auth.models.password_reset_log import PasswordResetLog
from client_auth.models.account_unlock_log import AccountUnlockLog
from client_auth.serializers.account_unlock_log_serializer import (
    AccountUnlockLogSerializer,
)
from client_auth.utils.common import (
    get_client_ip_and_agent,
    refresh_token_expiry_time,
    validate_password,
)
from client_auth.utils.token_utils import generate_tokens_for_client, blacklist_token
from django.core.validators import validate_email
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.exceptions import ValidationError
from django.conf import settings
from client_auth.utils.email_utils import send_reset_password_email
from client_auth.utils.token_utils import client_token_generator

token_generator = PasswordResetTokenGenerator()


def get_client_by_identifier(identifier):
    """Find client by email or phone."""
    if identifier.isdigit():
        return ClientManagement.objects.filter(phone=identifier).first()
    return ClientManagement.objects.filter(email__iexact=identifier).first()


def log_failed_attempt(username, ip, agent, reason):
    """Record failed login attempts."""
    LoginFailAttempt.objects.create(
        username=username,
        ip=ip,
        agent_browser=agent,
        client_details=reason,
        created_at=timezone.now(),
    )


def create_login_session(client, tokens, ip_address, user_agent, request):

    access_token_expiry = getattr(settings, "SIMPLE_JWT", {}).get(
        "ACCESS_TOKEN_LIFETIME", timedelta(hours=1)
    )
    refresh_token_expiry = getattr(settings, "SIMPLE_JWT", {}).get(
        "REFRESH_TOKEN_LIFETIME", timedelta(days=1)
    )

    session = LoginSession.objects.create(
        client=client,
        token=tokens["access"],
        refresh_token=tokens["refresh"],
        is_active=True,
        login_at=timezone.now(),
        access_expiry_at=timezone.now() + access_token_expiry,
        refresh_expiry_at=timezone.now() + refresh_token_expiry,
        ip_address=ip_address,
        agent_browser=user_agent,
        request_headers=dict(request.headers),
    )

    return session


class ClientLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("username")
        password = request.data.get("password")
        ip, agent = get_client_ip_and_agent(request)

        if not identifier or not password:
            return Response(
                {"success": False, "message": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = get_client_by_identifier(identifier)
        if not client:
            log_failed_attempt(identifier, ip, agent, {"reason": "Client not found"})
            return Response(
                {"success": False, "message": "Invalid credentials."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if getattr(client, "login_attempts", 0) >= MAX_LOGIN_ATTEMPTS:
            return Response(
                {
                    "success": False,
                    "message": "Account locked due to too many failed attempts.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not client.check_password(password):
            client.login_attempts = getattr(client, "login_attempts", 0) + 1
            client.save(update_fields=["login_attempts"])
            log_failed_attempt(client.email, ip, agent, {"reason": "Invalid password"})
            return Response(
                {"success": False, "message": "Invalid password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        client.login_attempts = 0
        client.save(update_fields=["login_attempts"])

        if getattr(client, "two_step", False):
            otp_code, expiry, request_id = send_login_otp(client)
            return Response(
                {
                    "success": True,
                    "message": "OTP sent successfully.",
                    "two_step": True,
                    "request_id": request_id,
                    "otp_expire": expiry,
                },
                status=status.HTTP_200_OK,
            )

        tokens = generate_tokens_for_client(client)

        session = create_login_session(client, tokens, ip, agent, request)

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "accessToken": tokens["access"],
                "refreshToken": tokens["refresh"],
                "two_step": False,
            },
            status=status.HTTP_200_OK,
        )


class ClientTwoFactorVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        client_id = request.data.get("client_id")
        otp_code = request.data.get("otp_code")

        if not client_id or not otp_code:
            return Response(
                {"success": False, "message": "client_id and otp_code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = ClientManagement.objects.get(id=client_id)
        except ClientManagement.DoesNotExist:
            return Response(
                {"success": False, "message": "Client not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp_record = (
            LoginOtpVerification.objects.filter(client=client, verified=False)
            .order_by("-id")
            .first()
        )

        if not otp_record:
            return Response(
                {"success": False, "message": "OTP not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if otp_record.status != DeliveryStatus.PENDING:
            return Response(
                {"success": False, "message": "OTP already used or invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if otp_record.otp_code != otp_code:
            return Response(
                {"success": False, "message": "Incorrect OTP."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if timezone.now() > otp_record.expires_at:
            otp_record.status = DeliveryStatus.EXPIRED
            otp_record.save(update_fields=["status"])
            return Response(
                {"success": False, "message": "OTP has expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        otp_record.status = DeliveryStatus.VERIFIED
        otp_record.verified = True
        otp_record.save(update_fields=["status", "verified"])

        client.login_attempts = 0
        client.save(update_fields=["login_attempts"])

        tokens = generate_tokens_for_client(client)

        ip, agent = get_client_ip_and_agent(request)
        session = create_login_session(client, tokens, ip, agent, request)

        return Response(
            {
                "success": True,
                "message": "OTP verified successfully.",
                "accessToken": tokens["access"],
                "refreshToken": tokens["refresh"],
            },
            status=status.HTTP_200_OK,
        )


class ClientForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"success": False, "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
            email = email.lower().strip()
        except ValidationError:
            return Response(
                {"success": False, "message": "Invalid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ip = request.META.get("REMOTE_ADDR", "")
        user_agent = request.headers.get("User-Agent", "")

        client = ClientManagement.objects.filter(email__iexact=email).first()

        if not client:

            return Response(
                {
                    "success": True,
                    "message": "If the email exists, a reset link has been sent.",
                },
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(client.id))
        token = client_token_generator.make_token(client)

        reset_link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?uid={uid}&token={token}"

        expires_at = timezone.now() + timedelta(hours=1)

        ForgotPassword.objects.create(
            client_id=client.id,
            token=token,
            ip_address=ip,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        try:
            send_reset_password_email(email, reset_link, user_name=client.name)
            return Response(
                {
                    "success": True,
                    "message": "If the email exists, a reset link has been sent.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"Failed to send email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ClientResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        ip, user_agent = get_client_ip_and_agent(request)

        missing_fields = []
        for field_name, value in {
            "uid": uidb64,
            "token": token,
            "new_password": new_password,
            "confirm_password": confirm_password,
        }.items():
            if not value:
                missing_fields.append(field_name)

        if missing_fields:
            return Response(
                {
                    "success": False,
                    "message": f"Missing required parameter(s): {', '.join(missing_fields)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {
                    "success": False,
                    "message": "New password and confirm password do not match.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response(
                {
                    "success": False,
                    "message": "Password validation failed.",
                    "errors": e.messages,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            client = ClientManagement.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, ClientManagement.DoesNotExist):
            return Response(
                {"success": False, "message": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_entry = (
            ForgotPassword.objects.filter(client=client).order_by("-created_at").first()
        )
        print(f" Found reset entry: {reset_entry}")
        if not reset_entry:
            return Response(
                {"success": False, "message": "No reset request found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reset_entry.token != token:
            return Response(
                {"success": False, "message": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reset_entry.ip_address != ip or reset_entry.user_agent != user_agent:
            return Response(
                {
                    "success": False,
                    "message": "IP address or user agent mismatch.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reset_entry.is_expired():
            return Response(
                {"success": False, "message": "Token has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(f"🔑 Resetting password for client ID {client.id}")
        try:
            client.set_password(new_password)
            client.save()
            print(f" Password updated successfully for client ID {client.id}")
        except Exception:
            return Response(
                {"success": False, "message": "Failed to reset password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            PasswordResetLog.objects.create(
                client_id=client.id,
                email=client.email,
                ip_address=ip,
                user_agent=user_agent,
                action="forgot_password_reset",
                successful=True,
                details="Password reset successfully via email link",
            )
        except Exception:
            return Response(
                {"success": False, "message": "Failed to log password reset."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            reset_entry.delete()
        except Exception:
            return Response(
                {"success": False, "message": "Failed to delete reset entry."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"success": True, "message": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )


class ClientAccountUnlockView(APIView):
    authentication_classes = [ClientJWTAuthentication]
    permission_classes = [AllowAny]
    authentication_classes = [ClientJWTAuthentication]

    def post(self, request):

        client_user = getattr(request, "client", None)

        email = request.data.get("email", "").strip()
        mobile = request.data.get("mobile_number", "").strip()
        name = request.data.get("name", "").strip()

        ip, agent = get_client_ip_and_agent(request)

        if not email:
            return Response(
                {"success": False, "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = ClientManagement.objects.filter(
            email__iexact=email,
            phone__iexact=mobile,
            name__iexact=name,
        ).first()

        if not client:

            AccountUnlockLog.objects.create(
                unlocked_by=client_user if client_user else None,
                unlocked_client=None,
                method="self" if not client_user else "admin",
                ip_address=ip,
                user_agent=agent,
                details=f"Unlock failed: client not found for {email}",
                success=False,
            )
            return Response(
                {"success": False, "message": "Invalid client details."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            client.login_attempts = 0
            client.status = 1
            client.save(update_fields=["login_attempts", "status"])

            log = AccountUnlockLog.objects.create(
                unlocked_by=client_user if client_user else None,
                unlocked_client=client,
                method="admin" if client_user else "self",
                ip_address=ip,
                user_agent=agent,
                details=f"Account for {client.email} unlocked successfully.",
                success=True,
            )

        serializer = AccountUnlockLogSerializer(log)
        return Response(
            {
                "success": True,
                "message": "Account unlocked successfully.",
                "log": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ClientChangePasswordView(APIView):

    authentication_classes = [ClientJWTAuthentication]
    permission_classes = [IsClientAuthenticated]

    def post(self, request):

        client = getattr(request, "client", None)
        print(f" Client attempting password change: {client}")
        if not client:
            return Response(
                {
                    "success": False,
                    "message": "Authentication failed or client not found.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        ip, agent = get_client_ip_and_agent(request)

        if not old_password or not new_password:
            return Response(
                {"success": False, "message": "Old and new passwords are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not client.check_password(old_password):
            PasswordResetLog.objects.create(
                client_id=client.id,
                email=client.email,
                ip_address=ip,
                user_agent=agent,
                action="change_password",
                successful=False,
                details="Incorrect old password.",
            )
            return Response(
                {"success": False, "message": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response(
                {"success": False, "message": "Weak password.", "errors": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_password == new_password:
            return Response(
                {
                    "success": False,
                    "message": "New password cannot be the same as old password.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            client.set_password(new_password)
            client.save(update_fields=["password"])

            PasswordResetLog.objects.create(
                client_id=client.id,
                email=client.email,
                ip_address=ip,
                user_agent=agent,
                action="change_password",
                successful=True,
                details="Password changed successfully.",
            )

        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class ClientLogoutView(APIView):
    authentication_classes = [ClientJWTAuthentication]
    permission_classes = [IsClientAuthenticated]

    def post(self, request):
        client = getattr(request, "client", None)
        if not client:
            return Response(
                {
                    "success": False,
                    "message": "Authentication required. Please log in to proceed.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_token = request.data.get("refresh")
        access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        ip, agent = get_client_ip_and_agent(request)

        if not refresh_token or not access_token:
            return Response(
                {
                    "success": False,
                    "message": "Both access token and refresh token are required for logout.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = LoginSession.objects.filter(
            token=access_token, client=client, is_active=True
        ).first()

        if not session:
            return Response(
                {
                    "success": False,
                    "message": "Your session has already been logged out. Please log in again.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.ip_address != ip or session.agent_browser != agent:
            return Response(
                {
                    "success": False,
                    "message": "Device or IP address mismatch detected. Access denied.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if BlacklistedToken.objects.filter(token=refresh_token).exists():
            return Response(
                {
                    "success": False,
                    "message": "The provided refresh token has been blacklisted.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        session.is_active = False
        session.logout_at = timezone.now()
        session.save(update_fields=["is_active", "logout_at"])

        blacklist_token(access_token, "access", client)
        blacklist_token(refresh_token, "refresh", client)

        return Response(
            {"success": True, "message": "You have been successfully logged out."},
            status=status.HTTP_200_OK,
        )
