from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from auth_system.models.user import TblUser


class ForgotPassword(models.Model):
    user = models.ForeignKey(TblUser, on_delete=models.SET_NULL, null=True, blank=True)
    token = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "auth_system_forgot_password"
    def is_expired(self):

        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Password reset for {self.user.email} on {self.created_at}"
