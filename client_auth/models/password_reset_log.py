from django.db import models
from django.utils import timezone
from kyc_api_gateway.models.client_management import ClientManagement

class PasswordResetLog(models.Model):
    client = models.ForeignKey(ClientManagement, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    action = models.CharField(max_length=50)  # forgot_password_requested, change_password
    timestamp = models.DateTimeField(default=timezone.now)
    successful = models.BooleanField(default=False)
    details = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "auth_client_password_reset_log"

    def __str__(self):
        return f"{self.email} - {self.action} - {self.timestamp}"
