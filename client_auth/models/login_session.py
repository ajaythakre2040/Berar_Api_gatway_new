from django.db import models
from django.utils import timezone
from kyc_api_gateway.models.client_management import ClientManagement


class LoginSession(models.Model):
    client = models.ForeignKey(ClientManagement, on_delete=models.CASCADE)
    token = models.CharField(max_length=1024, unique=True)
    refresh_token = models.CharField(
        max_length=1024, unique=True, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    login_at = models.DateTimeField(default=timezone.now)
    logout_at = models.DateTimeField(null=True, blank=True)
    access_expiry_at = models.DateTimeField(null=True, blank=True)
    refresh_expiry_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    agent_browser = models.CharField(max_length=255, null=True, blank=True)
    request_headers = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "auth_client_login_session"
        ordering = ["-login_at"]

    def __str__(self):
        status = "Active" if self.is_active else "Logged out"
        return f"[{status}] Client: {self.client.company_name} ({self.ip_address or 'N/A'})"

    @property
    def expiry_at(self):
        """
        Returns the earliest expiry time between access and refresh token expiry.
        If neither is available, returns None.
        """
        if self.access_expiry_at and self.refresh_expiry_at:
            return min(self.access_expiry_at, self.refresh_expiry_at)
        return self.access_expiry_at or self.refresh_expiry_at

    def is_expired(self):
        """
        Returns True if the session is expired based on either access or refresh token expiry.
        """
        now = timezone.now()
        if self.expiry_at and now > self.expiry_at:
            return True
        return False

    def mark_as_inactive(self):
        """
        Marks the session as inactive if expired or explicitly logged out.
        """
        if self.is_expired() or self.logout_at:
            self.is_active = False
            self.save()

    @classmethod
    def clean_up_expired_sessions(cls):
        """
        Cleans up expired sessions by marking them as inactive.
        """
        expired_sessions = cls.objects.filter(is_active=True).filter(
            models.Q(access_expiry_at__lt=timezone.now())
            | models.Q(refresh_expiry_at__lt=timezone.now())
        )
        for session in expired_sessions:
            session.mark_as_inactive()

    def validate_ip_and_agent(self, ip, agent_browser):
        """
        Validates that the current session matches the given IP and browser agent.
        Marks session as inactive if they don't match.
        """
        if self.ip_address != ip or self.agent_browser != agent_browser:
            self.is_active = False
            self.save()
            return False
        return True
