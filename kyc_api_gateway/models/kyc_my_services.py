from django.db import models


class KycMyServices(models.Model):
    name = models.CharField(max_length=255, unique=True)
    uat_url = models.CharField(max_length=255)
    prod_url = models.CharField(max_length=255)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_my_services"

    def __str__(self):
        return f"{self.name} (UAT: {self.uat_url})"