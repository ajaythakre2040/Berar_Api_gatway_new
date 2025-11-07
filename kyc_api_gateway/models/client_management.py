from django.db import models
from constant import STATUS_PENDING, USER_STATUS_CHOICES
from django.contrib.auth.hashers import make_password, check_password


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
    uat_key = models.CharField(max_length=255, unique=True, null=True)
    production_key = models.CharField(max_length=255, unique=True, null=True)
    password = models.CharField(max_length=255, default="")
    two_step = models.BooleanField(default=False)
    login_attempts = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "kyc_client_management"

    def __str__(self):
        return f"{self.company_name} ({self.email})"

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save(update_fields=["password"])

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        """Allow ClientManagement to be treated like a logged-in user"""
        return True
