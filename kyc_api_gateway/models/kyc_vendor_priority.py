from django.db import models


class KycVendorPriority(models.Model):
    client = models.ForeignKey(
        "ClientManagement",
        related_name="vendor_priorities",
        on_delete=models.CASCADE
    )

    vendor = models.ForeignKey(
        "VendorManagement",
        related_name="vendor_priority_entries",
        on_delete=models.CASCADE
    )

    my_service = models.ForeignKey(
        "KycMyServices",
        related_name="vendor_service_priorities",
        on_delete=models.CASCADE
    )

    priority = models.IntegerField(default=0)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_vendor_priority"
        ordering = ["priority"]

    def __str__(self):
        return f"{self.client} → {self.my_service} (Priority: {self.priority})"

