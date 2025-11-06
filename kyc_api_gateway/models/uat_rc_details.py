from django.db import models

class UatRcDetails(models.Model):
    request_id = models.CharField(max_length=100, null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)
    rc_number = models.CharField(max_length=20, db_index=True)
    case_id = models.CharField(max_length=100, null=True, blank=True)

    owner_name = models.CharField(max_length=255, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    owner_number = models.CharField(max_length=50, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    rc_status = models.CharField(max_length=50, null=True, blank=True)
    status_message = models.CharField(max_length=255, null=True, blank=True)
    masked_name = models.BooleanField(null=True, blank=True)

    registration_date = models.CharField(max_length=50, null=True, blank=True)
    registered_at = models.CharField(max_length=255, null=True, blank=True)
    vehicle_category = models.CharField(max_length=50, null=True, blank=True)
    vehicle_category_description = models.CharField(max_length=255, null=True, blank=True)
    vehicle_class_description = models.CharField(max_length=255, null=True, blank=True)
    rto_code = models.CharField(max_length=50, null=True, blank=True)
    variant = models.CharField(max_length=100, null=True, blank=True)

    maker_description = models.CharField(max_length=255, null=True, blank=True)
    maker_model = models.CharField(max_length=255, null=True, blank=True)
    body_type = models.CharField(max_length=100, null=True, blank=True)
    fuel_type = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    norms_type = models.CharField(max_length=100, null=True, blank=True)
    cubic_capacity = models.CharField(max_length=50, null=True, blank=True)
    vehicle_gross_weight = models.CharField(max_length=50, null=True, blank=True)
    unladen_weight = models.CharField(max_length=50, null=True, blank=True)
    no_cylinders = models.CharField(max_length=50, null=True, blank=True)
    seat_capacity = models.CharField(max_length=10, null=True, blank=True)
    sleeper_capacity = models.CharField(max_length=10, null=True, blank=True)
    standing_capacity = models.CharField(max_length=10, null=True, blank=True)
    wheelbase = models.CharField(max_length=50, null=True, blank=True)

    vehicle_chasi_number = models.CharField(max_length=100, null=True, blank=True)
    vehicle_engine_number = models.CharField(max_length=100, null=True, blank=True)

    manufacturing_date = models.CharField(max_length=50, null=True, blank=True)
    manufacturing_date_formatted = models.CharField(max_length=50, null=True, blank=True)
    manufactured_month_year = models.CharField(max_length=50, null=True, blank=True)

    insurance_company = models.CharField(max_length=255, null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=100, null=True, blank=True)
    insurance_upto = models.CharField(max_length=50, null=True, blank=True)

    tax_paid_upto = models.CharField(max_length=50, null=True, blank=True)
    tax_upto = models.CharField(max_length=50, null=True, blank=True)
    fit_up_to = models.CharField(max_length=50, null=True, blank=True)
    fitness_upto = models.CharField(max_length=50, null=True, blank=True)

    pucc_number = models.CharField(max_length=100, null=True, blank=True)
    pucc_upto = models.CharField(max_length=50, null=True, blank=True)
    puc_expiry_date = models.CharField(max_length=50, null=True, blank=True)

    permit_number = models.CharField(max_length=100, null=True, blank=True)
    permit_type = models.CharField(max_length=100, null=True, blank=True)
    permit_issue_date = models.CharField(max_length=50, null=True, blank=True)
    permit_valid_from = models.CharField(max_length=50, null=True, blank=True)
    permit_valid_upto = models.CharField(max_length=50, null=True, blank=True)
    national_permit_number = models.CharField(max_length=100, null=True, blank=True)
    national_permit_upto = models.CharField(max_length=50, null=True, blank=True)
    national_permit_issued_by = models.CharField(max_length=255, null=True, blank=True)

    non_use_status = models.CharField(max_length=50, null=True, blank=True)
    non_use_from = models.CharField(max_length=50, null=True, blank=True)
    non_use_to = models.CharField(max_length=50, null=True, blank=True)
    blacklist_status = models.CharField(max_length=255, null=True, blank=True)
    blacklist_info = models.JSONField(null=True, blank=True)

    financer = models.CharField(max_length=255, null=True, blank=True)
    financed = models.BooleanField(null=True, blank=True)

    present_address = models.TextField(null=True, blank=True)
    permanent_address = models.TextField(null=True, blank=True)

    less_info = models.BooleanField(default=False)
    response_metadata = models.JSONField(null=True, blank=True)
    latest_by = models.CharField(max_length=100, null=True, blank=True)
    profile_match = models.JSONField(null=True, blank=True)
    noc_details = models.TextField(null=True, blank=True)
    state_cd = models.CharField(max_length=50, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "uat_rc_details"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rc_number} - {self.owner_name or ''}"
