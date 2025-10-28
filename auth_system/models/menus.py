from django.db import models


class Menu(models.Model):

    menu_name = models.CharField(max_length=255 ,unique=True)
    menu_code = models.CharField(max_length=255, unique=True)
    sort_id = models.IntegerField(null=True, blank=True, unique=True)

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True, default=0)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True, default=0)

    class Meta:
        db_table = "auth_system_menus"

    def __str__(self):
        return self.menu_name
