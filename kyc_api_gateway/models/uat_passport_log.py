from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UatPassportRequestLog(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("success", "Success"),
        ("fail", "Fail"),
    )

    passport_verification = models.ForeignKey(
        "UatPassportDetails",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="passport_logs"
    )

    request_id = models.CharField(max_length=100, null=True, blank=True)
    file_number = models.CharField(max_length=100, null=True, blank=True)
    dob = models.CharField(max_length=20, null=True, blank=True)
    passport_number = models.CharField(max_length=50, null=True, blank=True)
    vendor = models.CharField(max_length=100, null=True, blank=True)
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
        db_table = "uat_passport_verification_request_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_number or 'N/A'} | {self.vendor or 'N/A'} | {self.status}"
