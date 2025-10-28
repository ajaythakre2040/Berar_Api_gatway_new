from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)               
    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True, default=None)
    deleted_by = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_system_department"

    def __str__(self):
        return f"{self.name}"
