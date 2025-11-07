from django.db import models
from django.utils import timezone


class LoginFailAttempt(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    agent_browser = models.TextField(null=True, blank=True)
    client_details = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "auth_client_login_fail_attempt"

    def __str__(self):
        return f"Failed login for {self.username} from {self.ip} at {self.created_at}"
