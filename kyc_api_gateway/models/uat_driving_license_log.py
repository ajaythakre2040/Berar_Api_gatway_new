from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UatDrivingLicenseRequestLog(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
    )

    driving_license = models.ForeignKey(
        "UatDrivingLicense",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dl_logs"
    )

    request_id = models.CharField(max_length=100, null=True, blank=True)
    dl_number = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    vendor = models.CharField(max_length=100, null=True, blank=True)
    endpoint = models.CharField(max_length=255, null=True, blank=True)

    status_code = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "uat_driving_license_request_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.dl_number or 'Unknown'} | {self.vendor or 'N/A'} | {self.status}"
