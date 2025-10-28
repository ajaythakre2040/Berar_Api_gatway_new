from django.db import models


class Role(models.Model):
    role_name = models.CharField(max_length=255, unique=True)
    role_code = models.CharField(max_length=255, unique=True)
    level = models.IntegerField(default=0)
    type = models.CharField(max_length=50,default='Custom')  # New field added
    description = models.TextField(null=True, blank=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True, default=0)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_system_roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ["-created_at"]

    def __str__(self):
        return self.role_name
