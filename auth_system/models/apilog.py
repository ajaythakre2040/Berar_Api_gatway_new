from django.db import models
from auth_system.models import TblUser


class APILog(models.Model):
    uniqid = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(TblUser, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(
        TblUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auth_system_apilogs",
    )
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=255)
    request_data = models.JSONField(null=True, blank=True)

    response_status = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.endpoint} ({self.response_status})"
