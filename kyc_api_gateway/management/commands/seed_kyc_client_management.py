from django.core.management.base import BaseCommand
from kyc_api_gateway.models import ClientManagement
from django.utils import timezone
from django.db import transaction, connection

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        clients = [
            {
                "company_name": "Booster",
                "business_type": "Private Limited",
                "registration_number": "REG890",
                "tax_id": "GSTIN789",
                "website": "https://booster.in",
                "industry": "IT Services",
                "name": "Aaqib Javed",
                "email": "aaqib@booster.in",
                "phone": "+91-9876543210",
                "position": "XYZ",
                "status": "1",
                "risk_level": "low",
                "compliance_level": "compliant",
                "production_key" :"XPUJ4jwzn3n5xxwjq9al",
                "uat_key" : 'XPUJ4jwzn3n5xxwjq9al',
            },
        ]

        for client in clients:
            try:
                with transaction.atomic():
                    obj = ClientManagement.objects.filter(company_name=client["company_name"]).first()
                    if obj:
                        obj.business_type = client["business_type"]
                        obj.registration_number = client["registration_number"]
                        obj.tax_id = client["tax_id"]
                        obj.website = client["website"]
                        obj.industry = client["industry"]
                        obj.name = client["name"]
                        obj.email = client["email"]
                        obj.phone = client["phone"]
                        obj.position = client["position"]
                        obj.status = client["status"]
                        obj.risk_level = client["risk_level"]
                        obj.compliance_level = client["compliance_level"]
                        obj.production_key = client["production_key"]
                        obj.uat_key = client["uat_key"]
                        obj.updated_by = 1
                        obj.updated_at = timezone.now()
                        obj.save()
                        self.stdout.write(self.style.SUCCESS(f"Updated existing client: {client['company_name']}"))
                    else:
                        # Create new client
                        ClientManagement.objects.create(
                            **client,
                            created_by=1,
                            created_at=timezone.now(),
                            updated_by=1,
                            updated_at=timezone.now()
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created new client: {client['company_name']}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to seed {client['company_name']}: {e}"))

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(
                    pg_get_serial_sequence('kyc_client_management', 'id'),
                    (SELECT COALESCE(MAX(id), 1) FROM kyc_client_management)
                )
            """)

        self.stdout.write(self.style.SUCCESS("ClientManagement production seeding completed successfully!"))
