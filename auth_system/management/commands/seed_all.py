# auth_system/management/commands/seed_all.py

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Run all seed commands in proper order: menu, role + permissions, then user"

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write(self.style.NOTICE("📁 Seeding menus..."))
            call_command("seed_menu")

            self.stdout.write(
                self.style.NOTICE("👑 Seeding admin role and permissions...")
            )
            call_command("seed_role_with_permissions")

            self.stdout.write(self.style.NOTICE("👤 Seeding admin user..."))
            call_command("seed_user")

            self.stdout.write(
                self.style.SUCCESS("✅ All seeders executed successfully!")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error occurred: {e}"))
