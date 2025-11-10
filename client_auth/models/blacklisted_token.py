from django.db import models
from kyc_api_gateway.models.client_management import ClientManagement
from django.utils import timezone

class BlacklistedToken(models.Model):
    TOKEN_CHOICES = (
        ("access", "Access"),
        ("refresh", "Refresh"),
    )

    client = models.ForeignKey(ClientManagement, on_delete=models.CASCADE)
    token = models.TextField(unique=True)
    token_type = models.CharField(max_length=10, choices=TOKEN_CHOICES)
    blacklisted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "client_auth_blacklistedtoken"

    def __str__(self):
        return f"{self.token_type} token for {self.client.company_name}"