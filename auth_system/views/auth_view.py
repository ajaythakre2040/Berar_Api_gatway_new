from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from auth_system.models.AccountUnlockLog import AccountUnlockLog
from auth_system.models.forgot_password import ForgotPassword
from auth_system.models.login_fail_attempts import LoginFailAttempts
from auth_system.models.password_reset_log import PasswordResetLog
from auth_system.models.user import TblUser
from auth_system.models.login_session import LoginSession
from auth_system.serializers.account_unlock_log_serializer import (
    AccountUnlockLogSerializer,
)
from auth_system.serializers.user import TblUserSerializer
from auth_system.throttles import ChangePasswordThrottle, ForgotPasswordThrottle
from auth_system.utils.token_utils import blacklist_token, generate_tokens_for_user
from auth_system.utils.common import get_client_ip_and_agent, refresh_token_expiry_time
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.db.models import Q
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from auth_system.utils.email_utils import send_reset_password_email
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from auth_system.utils.common import validate_password
from constant import MAX_LOGIN_ATTEMPTS
import re
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.db import transaction
from datetime import timedelta

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


def is_valid_mobile(identifier: str) -> bool:
    pattern = r"^\+?1?\d{9,15}$"
    return bool(re.match(pattern, identifier))


def get_user_by_identifier(identifier: str):
    if is_valid_mobile(identifier):
        return TblUser.objects.filter(mobile_number=identifier).first()
    return TblUser.objects.filter(Q(email=identifier) | Q(username=identifier)).first()


def log_failed_attempt(username, ip, agent, reason):
    LoginFailAttempts.objects.create(
        username=username,
        ip=ip,
        agent_browser=agent,
        user_details=reason,
        created_at=timezone.now(),
    )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("username")
        password = request.data.get("password")
        ip, agent = get_client_ip_and_agent(request)

        if not identifier or not password:
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Username (email/username/mobile) and password are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_user_by_identifier(identifier)
        if not user:
            log_failed_attempt(identifier, ip, agent, {"reason": "User not found"})
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "User not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "Account locked due to too many failed login attempts.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.check_password(password):
            user.login_attempts += 1
            user.save()
            log_failed_attempt(
                user.email,
                ip,
                agent,
                {
                    "reason": "Incorrect password",
                    "current_attempts": user.login_attempts,
                },
            )
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "message": "Incorrect password.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "message": "User account is inactive or disabled.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user.login_attempts = 0
        user.is_login = True
        user.save()

        tokens = generate_tokens_for_user(user)

        LoginSession.objects.create(
            user=user,
            token=tokens["access"],
            is_active=True,
            login_at=timezone.now(),
            expiry_at=refresh_token_expiry_time(),
            ip_address=ip,
            agent_browser=agent,
            request_headers=dict(request.headers),
        )

        return Response(
            {
                "success": True,
                "status_code": status.HTTP_200_OK,
                "message": "Login successful.",
                "accessToken": tokens["access"],
                "refreshToken": tokens["refresh"],
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        auth_header = request.headers.get("Authorization")

        if (
            not refresh_token
            or not auth_header
            or not auth_header.startswith("Bearer ")
        ):
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Both refresh and access tokens are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = auth_header.split(" ")[1]
        ip, agent = get_client_ip_and_agent(request)

        try:
            session = LoginSession.objects.filter(
                token=access_token, is_active=True
            ).first()
            if not session:
                return Response(
                    {
                        "success": False,
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Active session not found or user already logged out.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if session.ip_address != ip or session.agent_browser != agent:
                return Response(
                    {
                        "success": False,
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "message": "Logout request's IP or device does not match the login session.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            session.is_active = False
            session.logout_at = timezone.now()
            session.save()

            blacklist_token(refresh_token, token_type="refresh", user=request.user)
            blacklist_token(access_token, token_type="access", user=request.user)

            user = request.user
            user.is_login = False
            user.save(update_fields=["is_login"])

            return Response(
                {
                    "success": True,
                    "status_code": status.HTTP_200_OK,
                    "message": "Logout successful.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An unexpected error occurred during logout.",
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ForgotPasswordThrottle]

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

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:

            return Response(
                {
                    "success": True,
                    "message": "If the email exists, a reset link has been sent.",
                },
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?uid={uid}&token={token}"

        expires_at = timezone.now() + timedelta(hours=1)

        ForgotPassword.objects.create(
            user=user,
            token=token,
            ip_address=ip,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        try:
            send_reset_password_email(email, reset_link, user_name=user.first_name)
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


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ForgotPasswordThrottle]

    def post(self, request):

        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        ip, user_agent = get_client_ip_and_agent(request)

        missing_fields = []
        if not uidb64:
            missing_fields.append("uid")
        if not token:
            missing_fields.append("token")
        if not new_password:
            missing_fields.append("new_password")
        if not confirm_password:
            missing_fields.append("confirm_password")

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
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"success": False, "message": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reset_entry = (
                ForgotPassword.objects.filter(user=user).order_by("-created_at").first()
            )
        except Exception:
            return Response(
                {"success": False, "message": "Error while fetching reset entry."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
                {"success": False, "message": "IP address or user agent mismatch."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reset_entry.is_expired():
            return Response(
                {"success": False, "message": "Token has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user.set_password(new_password)
            user.save()
        except Exception:
            return Response(
                {"success": False, "message": "Failed to reset password."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            PasswordResetLog.objects.create(
                user=user,
                email=user.email,
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


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChangePasswordThrottle]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        ip, user_agent = get_client_ip_and_agent(request)

        if not old_password:
            return Response(
                {"success": False, "message": "Old password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not new_password:
            return Response(
                {"success": False, "message": "New password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            PasswordResetLog.objects.create(
                user=user,
                email=user.email,
                ip_address=ip,
                user_agent=user_agent,
                action="change_password",
                successful=False,
                details="Old password incorrect",
            )
            return Response(
                {"success": False, "message": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response(
                {
                    "success": False,
                    "message": "New password validation failed.",
                    "errors": e.messages,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_password == new_password:
            return Response(
                {
                    "success": False,
                    "message": "New password must be different from the old password.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        PasswordResetLog.objects.create(
            user=user,
            email=user.email,
            ip_address=ip,
            user_agent=user_agent,
            action="change_password",
            successful=True,
            details="Password changed successfully",
        )

        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class AccountUnlockView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        identifier = data.get("username", "").strip()
        first = data.get("first_name", "").strip()
        last = data.get("last_name", "").strip()
        mobile = data.get("mobile_number", "").strip()

        if not all([identifier, first, last, mobile]):
            return Response({"message": "All fields are required."}, status=400)

        ip, user_agent = get_client_ip_and_agent(request)

        user = TblUser.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier),
            first_name__iexact=first,
            last_name__iexact=last,
            mobile_number=mobile,
        ).first()

        if not user:
            AccountUnlockLog.objects.create(
                unlocked_by=request.user if request.user.is_authenticated else None,
                unlocked_user=None,
                method="admin" if request.user.is_authenticated else "self",
                ip_address=ip,
                user_agent=user_agent,
                details="Unlock failed: details did not match.",
                success=False,
            )
            return Response(
                {"message": "Details did not match. Account not unlocked."}, status=400
            )

        if user.login_attempts < 5:
            return Response(
                {
                    "message": "Your account is already active. No further activation is required."
                },
                status=200,
            )

        if request.user.is_authenticated:

            if request.user == user:

                method = "self"
                unlocked_by = request.user

            elif request.user.role_id.type == "System":
                method = "admin"
                unlocked_by = request.user
            else:
                return Response(
                    {"message": "You do not have permission to unlock this account."},
                    status=403,
                )

            user.login_attempts = 0
            user.is_active = True
            user.save(update_fields=["login_attempts", "is_active"])

            log = AccountUnlockLog.objects.create(
                unlocked_by=unlocked_by,
                unlocked_user=user,
                method=method,
                ip_address=ip,
                user_agent=user_agent,
                details=f"Account of {user.full_name} unlocked successfully.",
                success=True,
            )

            serializer = AccountUnlockLogSerializer(log)
            return Response(
                {"message": "Account unlocked successfully.", "log": serializer.data},
                status=200,
            )

        elif not request.user.is_authenticated:
            if user and identifier == data.get("username"):
                method = "self"
                unlocked_by = user

                user.login_attempts = 0
                user.is_active = True
                user.save(update_fields=["login_attempts", "is_active"])

                log = AccountUnlockLog.objects.create(
                    unlocked_by=unlocked_by,
                    unlocked_user=user,
                    method=method,
                    ip_address=ip,
                    user_agent=user_agent,
                    details=f"Account of {user.full_name} unlocked successfully.",
                    success=True,
                )

                serializer = AccountUnlockLogSerializer(log)
                return Response(
                    {
                        "message": "Account unlocked successfully.",
                        "log": serializer.data,
                    },
                    status=200,
                )
            else:
                return Response(
                    {"message": "Invalid account details or unauthorized access."},
                    status=400,
                )

        return Response(
            {"message": "Authentication required to unlock account."}, status=401
        )
