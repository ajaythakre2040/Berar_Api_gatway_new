from django.db import models


class UatAddressMatch(models.Model):
    request_id = models.CharField(max_length=100, null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)

    address1 = models.CharField(max_length=255, null=True, blank=True)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    match = models.BooleanField(null=True, blank=True)
    success = models.BooleanField(default=False)
    status_code = models.CharField(max_length=20, null=True, blank=True)
    message = models.CharField(max_length=255, null=True, blank=True)

    house = models.CharField(max_length=255, null=True, blank=True)
    locality = models.CharField(max_length=255, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    district = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    vendor_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "uat_address_match"
        ordering = ["-created_at"]

    def __str__(self):
        return f"AddressMatch [{self.vendor_name}] - {self.score or 'N/A'}"
