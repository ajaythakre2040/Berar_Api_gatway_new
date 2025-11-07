from django.db import models
from django.utils import timezone
from kyc_api_gateway.models.client_management import ClientManagement

class ForgotPassword(models.Model):
    client = models.ForeignKey(ClientManagement, on_delete=models.SET_NULL, null=True, blank=True)
    token = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "auth_client_forgot_password"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Password reset for {self.client.email if self.client else 'Unknown'}"
