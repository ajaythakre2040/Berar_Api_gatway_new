from django.db import models

class UatRcDetails(models.Model):
    request_id = models.CharField(max_length=100, null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)

    rc_number = models.CharField(max_length=30, db_index=True)
    owner_name = models.CharField(max_length=255, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    present_address = models.TextField(null=True, blank=True)
    permanent_address = models.TextField(null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)

    maker_description = models.CharField(max_length=255, null=True, blank=True)
    maker_model = models.CharField(max_length=255, null=True, blank=True)
    body_type = models.CharField(max_length=100, null=True, blank=True)
    fuel_type = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    norms_type = models.CharField(max_length=100, null=True, blank=True)
    vehicle_category = models.CharField(max_length=100, null=True, blank=True)
    vehicle_category_description = models.CharField(max_length=150, null=True, blank=True)

    vehicle_chasi_number = models.CharField(max_length=100, null=True, blank=True)
    vehicle_engine_number = models.CharField(max_length=100, null=True, blank=True)
    manufacturing_date = models.CharField(max_length=20, null=True, blank=True)
    manufacturing_date_formatted = models.CharField(max_length=20, null=True, blank=True)

    registration_date = models.CharField(max_length=20, null=True, blank=True)
    registered_at = models.CharField(max_length=255, null=True, blank=True)

    insurance_company = models.CharField(max_length=255, null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=100, null=True, blank=True)
    insurance_upto = models.CharField(max_length=20, null=True, blank=True)

    fit_upto = models.CharField(max_length=20, null=True, blank=True)
    tax_upto = models.CharField(max_length=20, null=True, blank=True)
    cubic_capacity = models.CharField(max_length=20, null=True, blank=True)
    vehicle_gross_weight = models.CharField(max_length=20, null=True, blank=True)
    unladen_weight = models.CharField(max_length=20, null=True, blank=True)
    seat_capacity = models.CharField(max_length=10, null=True, blank=True)
    sleeper_capacity = models.CharField(max_length=10, null=True, blank=True)
    standing_capacity = models.CharField(max_length=10, null=True, blank=True)
    wheelbase = models.CharField(max_length=20, null=True, blank=True)
    no_cylinders = models.CharField(max_length=10, null=True, blank=True)

    financer = models.CharField(max_length=255, null=True, blank=True)
    financed = models.BooleanField(null=True)

    rc_status = models.CharField(max_length=50, null=True, blank=True)
    latest_by = models.CharField(max_length=50, null=True, blank=True)
    less_info = models.BooleanField(null=True)

    full_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField()
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "uat_rc_details"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rc_number} - {self.owner_name or ''}"
