

# from django.core.management.base import BaseCommand
# from kyc_api_gateway.models import KycMyServices
# from django.utils import timezone
# from django.db import transaction, connection

# class Command(BaseCommand):
#     help = "Production-ready seeder for KycMyServices"

#     def handle(self, *args, **kwargs):
#         services = [
#             {
#                 "name": "PAN",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_pan_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_pan_details/"
#             },
#             {
#                 "name": "BILL",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_bill_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_bill_details/"
#             },
#             {
#                 "name": "VOTER",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_voter_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_voter_details/"
#             },
#             {
#                 "name": "Name",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_name_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_name_details/"
#             },
#             {
#                 "name": "RC",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_rc_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_rc_details/"
#             },
#             {
#                 "name": "DRIVING",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_driving_license_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_driving_license_details/"
#             },
#             {
#                 "name": "PASSPORT",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_passport_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_passport_details/"
#             },
#         ]

#         for service in services:
#             try:
#                 with transaction.atomic():
#                     obj = KycMyServices.objects.filter(name=service["name"]).first()
#                     if obj:
#                         # Update existing service
#                         obj.uat_url = service["uat_url"]
#                         obj.prod_url = service["prod_url"]
#                         obj.updated_by = 1
#                         obj.updated_at = timezone.now()
#                         obj.save()
#                         self.stdout.write(self.style.SUCCESS(f"Updated existing service: {service['name']}"))
#                     else:
#                         # Create new service
#                         KycMyServices.objects.create(
#                             name=service["name"],
#                             uat_url=service["uat_url"],
#                             prod_url=service["prod_url"],
#                             created_by=1,
#                             created_at=timezone.now(),
#                             updated_by=1,
#                             updated_at=timezone.now()
#                         )
#                         self.stdout.write(self.style.SUCCESS(f"Created new service: {service['name']}"))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Failed to seed {service['name']}: {e}"))

#         # Reset PostgreSQL sequence to prevent duplicate key issues
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT setval(
#                     pg_get_serial_sequence('kyc_my_services', 'id'),
#                     (SELECT COALESCE(MAX(id), 1) FROM kyc_my_services)
#                 )
#             """)

#         self.stdout.write(self.style.SUCCESS("KycMyServices production seeding completed successfully!"))



# from django.core.management.base import BaseCommand
# from kyc_api_gateway.models import KycMyServices
# from django.utils import timezone
# from django.db import transaction, connection

# class Command(BaseCommand):
#     help = "Production-ready seeder for KycMyServices"

#     def handle(self, *args, **kwargs):
#         services = [
#             {
#                 "name": "PAN",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_pan_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_pan_details/"
#             },
#             {
#                 "name": "BILL",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_bill_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_bill_details/"
#             },
#             {
#                 "name": "VOTER",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_voter_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_voter_details/"
#             },
#             {
#                 "name": "NAME",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_name_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_name_details/"
#             },
#             {
#                 "name": "RC",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_rc_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_rc_details/"
#             },
#             {
#                 "name": "DRIVING",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_driving_license_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_driving_license_details/"
#             },
#             {
#                 "name": "PASSPORT",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_passport_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_passport_details/"
#             },
#             {
#                 "name": "ADDRESS",
#                 "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_address_details/",
#                 "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_address_details/"
#             },
#         ]

#         for service in services:
#             try:
#                 with transaction.atomic():
#                     # Normalize name to uppercase for consistency
#                     name = service["name"].upper()

#                     # Case-insensitive lookup to avoid duplicates like "Name" vs "NAME"
#                     obj = KycMyServices.objects.filter(name__iexact=name).first()

#                     if obj:
#                         # Update existing service
#                         obj.uat_url = service["uat_url"]
#                         obj.prod_url = service["prod_url"]
#                         obj.updated_by = 1
#                         obj.updated_at = timezone.now()
#                         obj.save()
#                         self.stdout.write(self.style.SUCCESS(f"Updated existing service: {name}"))
#                     else:
#                         # Create new service
#                         KycMyServices.objects.create(
#                             name=name,
#                             uat_url=service["uat_url"],
#                             prod_url=service["prod_url"],
#                             created_by=1,
#                             created_at=timezone.now(),
#                             updated_by=1,
#                             updated_at=timezone.now()
#                         )
#                         self.stdout.write(self.style.SUCCESS(f"Created new service: {name}"))

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Failed to seed {service['name']}: {e}"))


#         # Reset PostgreSQL sequence to prevent duplicate key issues
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT setval(
#                     pg_get_serial_sequence('kyc_my_services', 'id'),
#                     (SELECT COALESCE(MAX(id), 1) FROM kyc_my_services)
#                 )
#             """)

#         self.stdout.write(self.style.SUCCESS("KycMyServices production seeding completed successfully!"))


from django.core.management.base import BaseCommand
from kyc_api_gateway.models import KycMyServices
from django.utils import timezone
from django.db import transaction, connection

class Command(BaseCommand):
    help = "Production-ready seeder for KycMyServices (auto-fills missing IDs)"

    def handle(self, *args, **kwargs):
        services = [
            {
                "name": "PAN",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_pan_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_pan_details/"
            },
            {
                "name": "BILL",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_bill_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_bill_details/"
            },
            {
                "name": "VOTER",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_voter_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_voter_details/"
            },
            {
                "name": "NAME",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_name_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_name_details/"
            },
            {
                "name": "RC",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_rc_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_rc_details/"
            },
            {
                "name": "DRIVING",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_driving_license_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_driving_license_details/"
            },
            {
                "name": "PASSPORT",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_passport_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_passport_details/"
            },
            {
                "name": "ADDRESS",
                "uat_url": "http://127.0.0.1:8000/kyc_api_gateway/uat_address_details/",
                "prod_url": "http://127.0.0.1:8000/kyc_api_gateway/pro_address_details/"
            },
        ]

        try:
            with transaction.atomic():
                existing_services = {s.name.upper(): s for s in KycMyServices.objects.all()}

                for service in services:
                    name = service["name"].upper()
                    if name in existing_services:
                        # Update existing record
                        obj = existing_services[name]
                        obj.uat_url = service["uat_url"]
                        obj.prod_url = service["prod_url"]
                        obj.updated_by = 1
                        obj.updated_at = timezone.now()
                        obj.save()
                        self.stdout.write(self.style.SUCCESS(f"✅ Updated: {name}"))
                    else:
                        # Create missing record
                        KycMyServices.objects.create(
                            name=name,
                            uat_url=service["uat_url"],
                            prod_url=service["prod_url"],
                            created_by=1,
                            created_at=timezone.now(),
                            updated_by=1,
                            updated_at=timezone.now()
                        )
                        self.stdout.write(self.style.SUCCESS(f"🆕 Created: {name}"))

                # ✅ Reset sequence after inserts
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT setval(
                            pg_get_serial_sequence('kyc_my_services', 'id'),
                            (SELECT COALESCE(MAX(id), 1) FROM kyc_my_services)
                        )
                    """)

                self.stdout.write(self.style.SUCCESS("\n🎯 KycMyServices seeding completed successfully!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Seeding failed: {e}"))