from django.urls import path
from client_auth.views.client_auth_view import (
    ClientLoginView,
    ClientLogoutView,
    ClientChangePasswordView,
    ClientForgotPasswordView,
    ClientResetPasswordView,
    ClientAccountUnlockView,
    ClientTwoFactorVerifyView,
)

urlpatterns = [
    path("login/", ClientLoginView.as_view(), name="client-login"),
    path("verify-otp/", ClientTwoFactorVerifyView.as_view(), name="client-verify-otp"),
    path("logout/", ClientLogoutView.as_view(), name="client-logout"),
    path(
        "change-password/",
        ClientChangePasswordView.as_view(),
        name="client-change-password",
    ),
    path(
        "forgot-password/",
        ClientForgotPasswordView.as_view(),
        name="client-forgot-password",
    ),
    path(
        "reset-password/",
        ClientResetPasswordView.as_view(),
        name="client-reset-password",
    ),
    path(
        "account-unlock/",
        ClientAccountUnlockView.as_view(),
        name="client-account-unlock",
    ),
]
