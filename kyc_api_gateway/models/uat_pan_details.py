from django.db import models

class UatPanDetails(models.Model):
    request_id = models.CharField(max_length=100, null=True, blank=True)
    client_id = models.CharField(
        max_length=100, null=True, blank=True
    )  
    pan_number = models.CharField(max_length=20, db_index=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    aadhaar_linked = models.BooleanField(null=True)
    masked_aadhaar = models.CharField(max_length=20, null=True, blank=True)
    aadhaar_match = models.BooleanField(null=True)

    dob = models.DateField(null=True, blank=True)
   
    dob_verified = models.BooleanField(null=True)
    dob_check = models.BooleanField(null=True)

    gender = models.CharField(max_length=10, null=True, blank=True)

    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    pan_status = models.CharField(max_length=50, null=True, blank=True)
    is_salaried = models.BooleanField(null=True)
    is_director = models.BooleanField(null=True)
    is_sole_prop = models.BooleanField(null=True)
    issue_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)  
    less_info = models.BooleanField(null=True)

    profile_match = models.JSONField(null=True, blank=True)

    address_line_1 = models.CharField(
        max_length=255, null=True, blank=True
    )  
    address_line_2 = models.CharField(
        max_length=255, null=True, blank=True
    )  
    street_name = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pin_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=100, default="INDIA")
    full_address = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = "uat_pan_details" 
        ordering = ["-created_at"] 


    def __str__(self):
        return f"{self.pan_number} - {self.full_name or ''}"
