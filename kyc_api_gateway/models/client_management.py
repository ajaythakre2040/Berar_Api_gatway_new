from django.db import models

from constant import STATUS_PENDING, USER_STATUS_CHOICES


class ClientManagement(models.Model):
    company_name = models.CharField(max_length=255, unique=True)
    business_type = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=255, unique=True)
    tax_id = models.CharField(max_length=20, unique=True)
    website = models.CharField(max_length=255, unique=True)
    industry = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    position = models.CharField(max_length=255)
    status = models.IntegerField(
        choices=USER_STATUS_CHOICES,  
        default=STATUS_PENDING,
    )
    risk_level = models.CharField(max_length=100)
    compliance_level = models.CharField(max_length=100)
    uat_key = models.CharField(max_length=255, unique=True, null=True,)
    production_key = models.CharField(max_length=255, unique=True, null=True,)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_client_management"

    def __str__(self):
        return f"{self.company_name} ({self.business_type})"
