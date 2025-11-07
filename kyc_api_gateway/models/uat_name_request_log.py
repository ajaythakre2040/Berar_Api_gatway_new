from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UatNameMatchRequestLog(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
    )

    name_match = models.ForeignKey(
        "UatNameMatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="name_match_logs"
    )

    request_id = models.CharField(max_length=100, null=True, blank=True)
    name_1 = models.CharField(max_length=200, null=True, blank=True)
    name_2 = models.CharField(max_length=200, null=True, blank=True)

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
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "uat_name_match_request_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name_1 or 'Unknown'} ↔ {self.name_2 or 'Unknown'} | {self.vendor or 'N/A'} | {self.status}"
