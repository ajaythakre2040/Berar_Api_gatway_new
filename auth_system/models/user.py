import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email is required.")
        if not extra_fields.get("mobile_number"):
            raise ValueError("The mobile number is required.")
        if not extra_fields.get("first_name") or not extra_fields.get("last_name"):
            raise ValueError("Full name (first and last) is required.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class TblUser(AbstractBaseUser, PermissionsMixin):
    mobile_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Enter a valid mobile number."
    )

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        validators=[mobile_regex],
    )
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, unique=True)

    role_id = models.ForeignKey(
        "auth_system.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users_role",
        db_column="role_id",
    )

    status = models.IntegerField(default=0)
    timezone = models.CharField(max_length=255, default="UTC", blank=True, null=True)
    timeout = models.CharField(default="30", max_length=100)
    
    department = models.ForeignKey(
        "auth_system.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_role",
        db_column="department_id",
    )
    position = models.CharField(max_length=255)
    login_attempts = models.IntegerField(default=0)
    is_login= models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # login_attempts = models.IntegerField(default=0)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["mobile_number", "first_name", "last_name"]

    class Meta:
        db_table = "auth_system_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def full_info(self):

        return (
            f"{self.first_name} {self.last_name} - {self.mobile_number} - {self.email}"
        )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
