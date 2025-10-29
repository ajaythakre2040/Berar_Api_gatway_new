from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UatPassportDetails(models.Model):
    client_id = models.CharField(max_length=100, null=True, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    
    passport_number = models.CharField(max_length=50, null=True, blank=True)
    file_number = models.CharField(max_length=100, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    surname = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    
    date_of_issue = models.DateField(null=True, blank=True)
    date_of_application = models.DateField(null=True, blank=True)
    application_type = models.CharField(max_length=100, null=True, blank=True)
    status_text = models.TextField(null=True, blank=True)

    vendor = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "uat_passport_details"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name or 'Unknown'} ({self.passport_number or 'N/A'})"
