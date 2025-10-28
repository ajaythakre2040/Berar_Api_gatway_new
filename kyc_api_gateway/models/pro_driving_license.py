from django.db import models

class ProDrivingLicense(models.Model):
    client_id = models.CharField(max_length=100, null=True, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)

    dl_number = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    father_name = models.CharField(max_length=200, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    valid_till = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    rto_code = models.CharField(max_length=50, null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)

    dl_status = models.CharField(max_length=50, null=True, blank=True)
    issuing_authority = models.CharField(max_length=200, null=True, blank=True)
    non_transport_validity = models.DateField(null=True, blank=True)
    transport_validity = models.DateField(null=True, blank=True)

    photo = models.TextField(null=True, blank=True) 
    signature = models.TextField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    vendor_name = models.CharField(max_length=100, null=True, blank=True)
    full_response = models.JSONField(null=True, blank=True)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pro_driving_license"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name or 'Unknown'} ({self.dl_number or 'No DL'})"
