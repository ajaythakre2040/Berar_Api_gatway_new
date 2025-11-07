from django.db import models
from django.utils import timezone
from kyc_api_gateway.models.client_management import ClientManagement


class APILog(models.Model):
    uniqid = models.CharField(max_length=100, db_index=True)
    client = models.ForeignKey(ClientManagement, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=255)
    request_data = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_client_api_log"

    def __str__(self):
        return f"{self.method} {self.endpoint} ({self.response_status})"
