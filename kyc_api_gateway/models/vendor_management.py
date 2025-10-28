from django.db import models
from django.utils import timezone
class VendorManagement(models.Model):


    vendor_name = models.CharField(max_length=255, unique=False)
    header_key_name = models.CharField(max_length=255, null=True, blank=True)
    uat_base_url = models.CharField(max_length=255, null=True, blank=True)
    uat_api_key = models.CharField(max_length=255, null=True, blank=True)
    prod_base_url = models.CharField(max_length=255, null=True, blank=True)
    prod_api_key = models.CharField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=10,blank=True, null=True,unique=False)
    contact_email = models.EmailField(max_length=255,unique=False,blank=True, null=True)
    status = models.BooleanField(default=False)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "kyc_vendor_management"

    def __str__(self):
        return self.vendor_name

    def __str__(self):
        return self.vendor_name
    
    def soft_delete(self, user_id):
        self.deleted_at = timezone.now()
        self.deleted_by = user_id
        self.save()

    @property
    def is_active(self):
        return self.status.lower() == "active" and self.deleted_at is None







