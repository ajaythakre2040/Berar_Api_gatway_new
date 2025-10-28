# auth_system/management/commands/seed_role_with_permissions.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from auth_system.models.role import Role
from auth_system.models.role_permission import RolePermission
from auth_system.models.menus import Menu


class Command(BaseCommand):
    help = "Seed Admin role and assign full permissions for all menus"

    def handle(self, *args, **kwargs):
        # Create Admin Role
        admin_role, created = Role.objects.get_or_create(
            role_code="ADMIN",
            defaults={
                "role_name": "Admin",
                "level": 1,
                "type": "System",
                "description": "Administrator role with all permissions",
                "created_by": 1,
                "created_at": timezone.now(),
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("✅ Admin role created"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Admin role already exists"))

        # Assign Full Permissions to All Menus
        menus = Menu.objects.filter(deleted_at__isnull=True)
        for menu in menus:
            permission, created = RolePermission.objects.get_or_create(
                role=admin_role,
                menu_id=menu,
                defaults={
                    "view": True,
                    "add": True,
                    "edit": True,
                    "delete": True,
                    "print": True,
                    "export": True,
                    "sms_send": True,
                    "api_limit": "",
                    "created_by": 1,
                    "created_at": timezone.now(),
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Permission added for menu: {menu.menu_name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Permission already exists for menu: {menu.menu_name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("🎯 Admin role and all permissions seeded successfully.")
        )
