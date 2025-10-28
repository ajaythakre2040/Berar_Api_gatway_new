from django.db import models
from django.utils import timezone

from .user import TblUser  


class LoginSession(models.Model):

    user = models.ForeignKey(TblUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=1024, unique=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    login_at = models.DateTimeField(default=timezone.now)
    logout_at = models.DateTimeField(null=True, blank=True)
    expiry_at = models.DateTimeField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    agent_browser = models.CharField(max_length=255, null=True, blank=True)
    request_headers = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "auth_system_login_session"
        indexes = [
            models.Index(fields=["user", "logout_at"]),
        ]
        ordering = ["-login_at"]
        verbose_name = "Login Session"
        verbose_name_plural = "Login Sessions"

    def __str__(self):
        status = "Active" if self.is_active else "Logged out"
        return f"[{status}] User: {self.user_id} - IP: {self.ip_address or 'N/A'}"

    def is_expired(self):
        """Check whether the session is expired based on expiry_at."""
        return self.expiry_at and timezone.now() > self.expiry_at
