from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UatAddressMatchRequestLog(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
    )

    address_match = models.ForeignKey(
        "UatAddressMatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="address_logs"
    )

    address1 = models.CharField(max_length=255, null=True, blank=True)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    vendor = models.CharField(max_length=100, null=True, blank=True)
    endpoint = models.CharField(max_length=255, null=True, blank=True)

    status_code = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    user_agent = models.CharField(max_length=512, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "uat_address_match_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.address1 or 'Unknown'} ↔ {self.address2 or 'Unknown'} | {self.vendor or 'N/A'} | {self.status}"
