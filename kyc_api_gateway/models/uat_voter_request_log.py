from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class UatVoterRequestLog(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
    )

    voter_detail = models.ForeignKey(
        "UatVoterDetail",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bill_logs"
    )
    vendor = models.CharField(max_length=50, null=True, blank=True)
    endpoint = models.CharField(max_length=255, null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    user_agent = models.CharField(max_length=512, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "uat_voter_request_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vendor or 'N/A'} | {self.status}"
