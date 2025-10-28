from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UatRcRequestLog(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
    )

    rc_details = models.ForeignKey(
        "UatRcDetails",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    rc_number = models.CharField(max_length=30, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    vendor = models.CharField(max_length=50, null=True, blank=True)
    endpoint = models.CharField(max_length=200)
    status_code = models.IntegerField()
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    user_agent = models.CharField(max_length=512, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "uat_rc_request_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rc_number} | {self.vendor} | {self.status}"
