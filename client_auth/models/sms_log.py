from django.db import models
from django.utils import timezone

from constant import DeliveryStatus, SmsType

class SmsLog(models.Model):
    user_id = models.CharField(max_length=50, null=True, blank=True)
    mobile_number = models.CharField(max_length=15)
    message = models.TextField()
    sms_type = models.IntegerField(choices=SmsType.choices)
    request_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.IntegerField(choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "auth_client_sms_log"

    def __str__(self):
        return f"SMS to {self.mobile_number} [{self.get_status_display()}]"
