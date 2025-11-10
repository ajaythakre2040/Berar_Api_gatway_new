from django.db import models
from django.utils import timezone
from kyc_api_gateway.models.client_management import ClientManagement

class LoginSession(models.Model):
    client = models.ForeignKey(ClientManagement, on_delete=models.CASCADE)
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
        db_table = "auth_client_login_session"
        ordering = ["-login_at"]

    def __str__(self):
        status = "Active" if self.is_active else "Logged out"
        return f"[{status}] Client: {self.client.company_name} ({self.ip_address or 'N/A'})"

    def is_expired(self):
        return self.expiry_at and timezone.now() > self.expiry_at
