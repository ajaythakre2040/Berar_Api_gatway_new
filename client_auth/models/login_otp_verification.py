from django.db import models
from django.utils import timezone

from constant import DeliveryStatus

class LoginOtpVerification(models.Model):
    client = models.ForeignKey("kyc_api_gateway.ClientManagement", on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    request_id = models.CharField(max_length=100, unique=True)
    status = models.IntegerField(choices=DeliveryStatus.choices)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "auth_client_login_otp_verification"

    def is_expired(self):
        return timezone.now() > self.expires_at
