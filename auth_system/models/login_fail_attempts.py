from django.db import models


class LoginFailAttempts(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    agent_browser = models.TextField(null=True, blank=True)
    user_details = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_system_login_fail_attempts"

    def __str__(self):
        return f"Failed login attempt for {self.username} from {self.ip} at {self.created_at}"
