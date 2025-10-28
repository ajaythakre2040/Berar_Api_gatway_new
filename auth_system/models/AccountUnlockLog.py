from django.db import models
from django.conf import settings
from django.utils import timezone


class AccountUnlockLog(models.Model):
    METHOD_CHOICES = [
        ("self", "Self Unlock"),
        ("admin", "Admin Unlock"),
    ]

    unlocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="unlock_performed",
        help_text="User who performed the unlock action (admin/staff), or blank for self.",
    )
    unlocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="unlock_received",
        help_text="User whose account was attempted to be unlocked.",
    )
    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        help_text="Indicates whether it was a self unlock or admin unlock.",
    )
    timestamp = models.DateTimeField(
        default=timezone.now, help_text="Time when the unlock was attempted."
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from where the unlock was requested.",
    )
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="User-Agent string of the request.",
    )
    success = models.BooleanField(
        default=False, help_text="Whether the unlock attempt was successful."
    )
    details = models.TextField(
        null=True, blank=True, help_text="Any notes or reason for failure/success."
    )

    class Meta:
        verbose_name = "Account Unlock Log"
        verbose_name_plural = "Account Unlock Logs"
        ordering = ["-timestamp"]
        db_table = "auth_system_account_unlock_log"

    def __str__(self):
        status = "✅ Success" if self.success else "❌ Failed"
        who = self.unlocked_by.get_full_name() if self.unlocked_by else "Self"
        target = (
            self.unlocked_user.get_full_name() if self.unlocked_user else "Unknown User"
        )
        return (
            f"{status} | {who} → {target} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        )
