from django.db import models
from auth_system.models.menus import Menu
from auth_system.models.role import Role


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    menu_id = models.ForeignKey(
        Menu, on_delete=models.CASCADE, related_name="role_permissions", db_column="menu_id"
    )

    view = models.BooleanField(default=False)
    add = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    print = models.BooleanField(default=False)
    export = models.BooleanField(default=False)
    sms_send = models.BooleanField(default=False)
    api_limit = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True, default=0)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_system_role_permissions"
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
        ordering = ["-created_at"]
        
        
        
        indexes = [
            models.Index(fields=['role_id', 'menu_id'], name='unique_role_menu_active', condition=models.Q(deleted_at__isnull=True)),
        ]

    def __str__(self):
        return f"Permission: Role {self.role_id} - Menu {self.menu_id}"
