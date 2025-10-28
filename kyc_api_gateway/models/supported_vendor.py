from django.db import models
from django.utils import timezone
from kyc_api_gateway.models.vendor_management import VendorManagement


class SupportedVendor(models.Model):
    api = models.ForeignKey("ApiManagement", on_delete=models.CASCADE)
    vendor = models.ForeignKey(VendorManagement, on_delete=models.CASCADE)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_supported_vendor"
        unique_together = ("api", "vendor")
