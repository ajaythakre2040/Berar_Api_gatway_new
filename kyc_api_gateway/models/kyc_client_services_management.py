from django.db import models


class KycClientServicesManagement(models.Model):
    client = models.ForeignKey(
        "ClientManagement",
        related_name="client_services",
        on_delete=models.CASCADE
    )
    myservice = models.ForeignKey(
        "KycMyServices",
        related_name="kyc_services",
        on_delete=models.CASCADE
    )
    
    uat_api_limit = models.CharField(default=100)
    status = models.BooleanField(default=True)
    day =  models.IntegerField(default=0)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_client_services_management"
    def __str__(self):
        return f"{self.client} → {self.myservice} ({self.status})"