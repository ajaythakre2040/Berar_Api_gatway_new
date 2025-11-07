from django.db import models
from kyc_api_gateway.models.client_management import ClientManagement


class AccountUnlockLog(models.Model):
    METHOD_CHOICES = [
        ("self", "Self Unlock"),
        ("admin", "Admin Unlock"),
    ]

    unlocked_by = models.ForeignKey(
        ClientManagement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="client_unlock_performed",
    )
    unlocked_client = models.ForeignKey(
        ClientManagement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="client_unlock_received",
    )
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    success = models.BooleanField(default=False)
    details = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "auth_client_account_unlock_log"
        ordering = ["-timestamp"]

    def __str__(self):
        status = "✅ Success" if self.success else "❌ Failed"
        who = self.unlocked_by.company_name if self.unlocked_by else "Self"
        target = self.unlocked_client.company_name if self.unlocked_client else "Unknown"
        return f"{status} | {who} → {target} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
