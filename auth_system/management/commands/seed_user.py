# auth_system/management/commands/seed_user.py

from django.core.management.base import BaseCommand
from auth_system.models.user import TblUser
from auth_system.models.role import Role
from auth_system.models.department import Department
from django.utils import timezone
from constant import ADMIN_USER


class Command(BaseCommand):
    help = "Seed the admin user into the database"

    def handle(self, *args, **kwargs):
        email = ADMIN_USER["email"]
        password = ADMIN_USER["password"]

        if TblUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"⚠️ Admin already exists: {email}"))
            return

        try:
            role = Role.objects.get(role_code="ADMIN")
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Admin role not found. Please run seed_role_with_permissions first."
                )
            )
            return

        department = None
        if ADMIN_USER.get("department_id"):
            try:
                department = Department.objects.get(id=ADMIN_USER["department_id"])
            except Department.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING("⚠️ Department ID not found. Skipping.")
                )

        TblUser.objects.create_superuser(
            first_name=ADMIN_USER["first_name"],
            last_name=ADMIN_USER["last_name"],
            email=email,
            mobile_number=ADMIN_USER["mobile_number"],
            username=ADMIN_USER["username"],
            password=password,
            role_id=role,
            department=department,
            position=ADMIN_USER.get("position", "Admin"),
            status=1,
            created_at=timezone.now(),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Admin user created\n📧 Email: {email}\n🔑 Password: {password}"
            )
        )
