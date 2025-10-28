from django.db import models
from kyc_api_gateway.models.vendor_management import VendorManagement


class ApiManagement(models.Model):
    api_name = models.CharField(max_length=255, unique=True)
    endpoint_path = models.CharField(max_length=255, unique=True)
    http_method = models.CharField(max_length=10)

    vendor = models.ForeignKey(
        VendorManagement,
        related_name="default_apis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    descriptions = models.TextField(null=True, blank=True)
    enable_api_endpoint = models.BooleanField(default=True)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_api_management"

    def __str__(self):
        return self.api_name
