# file: auth_system/management/commands/seed_menu.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from auth_system.models.menus import Menu


class Command(BaseCommand):
    help = "Seed initial menu data"

    def handle(self, *args, **kwargs):
        menus = [
            {"menu_name": "Dashboard", "menu_code": "DASHBOARD", "sort_id": 1},
            {"menu_name": "Users", "menu_code": "USERS", "sort_id": 2},
            {"menu_name": "Roles", "menu_code": "ROLES", "sort_id": 3},
            {"menu_name": "Clients", "menu_code": "CLIENTS", "sort_id": 4},
            {"menu_name": "API", "menu_code": "API", "sort_id": 5},
            {"menu_name": "Vendors", "menu_code": "VENDORS", "sort_id": 6},
            {"menu_name": "System", "menu_code": "SYSTEM", "sort_id": 7},
            {"menu_name": "Reports", "menu_code": "REPORTS", "sort_id": 8},
        ]

        for menu in menus:
            obj, created = Menu.objects.get_or_create(
                menu_name=menu["menu_name"],
                defaults={
                    "menu_code": menu["menu_code"],
                    "sort_id": menu["sort_id"],
                    "created_by": 1,  # Update later if needed
                    "created_at": timezone.now(),
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created menu: {menu["menu_name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Menu already exists: {menu["menu_name"]}')
                )
# auth_system/management/commands/seed_menu.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from auth_system.models.menus import Menu


class Command(BaseCommand):
    help = "Seed initial menu data"

    def handle(self, *args, **kwargs):
        menus = [
            {"menu_name": "Dashboard", "menu_code": "DASHBOARD", "sort_id": 1},
            {"menu_name": "Users", "menu_code": "USERS", "sort_id": 2},
            {"menu_name": "Roles", "menu_code": "ROLES", "sort_id": 3},
            {"menu_name": "Clients", "menu_code": "CLIENTS", "sort_id": 4},
            {"menu_name": "API", "menu_code": "API", "sort_id": 5},
            {"menu_name": "Vendors", "menu_code": "VENDORS", "sort_id": 6},
            {"menu_name": "System", "menu_code": "SYSTEM", "sort_id": 7},
            {"menu_name": "Reports", "menu_code": "REPORTS", "sort_id": 8},
        ]

        for menu in menus:
            obj, created = Menu.objects.get_or_create(
                menu_name=menu["menu_name"],
                defaults={
                    "menu_code": menu["menu_code"],
                    "sort_id": menu["sort_id"],
                    "created_by": 1,
                    "created_at": timezone.now(),
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created menu: {menu["menu_name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Menu already exists: {menu["menu_name"]}')
                )
