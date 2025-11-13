from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from kyc_api_gateway.models import KycVendorPriority
from kyc_api_gateway.models.kyc_client_services_management import KycClientServicesManagement
from kyc_api_gateway.serializers.Kyc_vendor_priority_serializer import (
    KycVendorPrioritySerializer,
)
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination
from kyc_api_gateway.serializers.kyc_client_services_management_serializer import KycClientServicesManagementSerializer
from django.db import transaction


class KycVendorPriorityListCreate(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()
        records = KycVendorPriority.objects.filter(deleted_at__isnull=True)

        if search_query:
            records = records.filter(
                Q(client__name__icontains=search_query)
                | Q(vendor__vendor_name__icontains=search_query)
                | Q(my_service__name__icontains=search_query)
            )

        records = records.order_by("priority")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(records, request)
        serializer = KycVendorPrioritySerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Vendor priority list retrieved successfully.",
            },
        )

  
    def post(self, request):
        client_id = request.data.get("client_id")
        service_data_list = request.data.get("my_service_data", [])

        if not client_id or not service_data_list:
            return Response(
                {
                    "success": False,
                    "message": "Missing 'client_id' or 'my_service_data' in request.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service_ids = [s.get("my_service_id") for s in service_data_list if s.get("my_service_id")]
            if not service_ids:
                return Response(
                    {
                        "success": False,
                        "message": "Each service entry must include 'my_service_id'.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(service_ids) != len(set(service_ids)):
                return Response(
                    {
                        "success": False,
                        "message": "Duplicate 'my_service_id' found in request.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                created_client_services = []
                created_vendor_priorities = []

                for service_data in service_data_list:
                    my_service_id = service_data.get("my_service_id")
                    vendor_data_list = service_data.get("vendor_data", [])
                    repated_day = service_data.get("repated_day", 0)

                    if not my_service_id:
                        raise ValueError("Missing 'my_service_id' in one of the entries.")

                    if not vendor_data_list:
                        raise ValueError(f"'vendor_data' is required for service ID {my_service_id}.")

                    vendor_ids = [v.get("vendor_id") for v in vendor_data_list if v.get("vendor_id")]
                    if len(vendor_ids) != len(set(vendor_ids)):
                        raise ValueError(f"Duplicate 'vendor_id' found for service ID {my_service_id}.")

                    priorities = [v.get("priority") for v in vendor_data_list if v.get("priority") is not None]
                    if len(priorities) != len(set(priorities)):
                        raise ValueError(f"Duplicate 'priority' values found for service ID {my_service_id}.")

                    if KycClientServicesManagement.objects.filter(
                        client_id=client_id, myservice_id=my_service_id
                    ).exists():
                        raise ValueError(
                            f"Service already exists for Client ID {client_id} and Service ID {my_service_id}."
                        )

                    for vendor_data in vendor_data_list:
                        vendor_id = vendor_data.get("vendor_id")
                        priority = vendor_data.get("priority")

                        if not vendor_id or priority is None:
                            raise ValueError(
                                f"Each vendor entry for Service ID {my_service_id} must include both 'vendor_id' and 'priority'."
                            )

                        if KycVendorPriority.objects.filter(
                            client_id=client_id,
                            my_service_id=my_service_id,
                            vendor_id=vendor_id,
                        ).exists():
                            raise ValueError(
                                f"Duplicate entry found for Client ID {client_id}, Service ID {my_service_id}, and Vendor ID {vendor_id}."
                            )

                    client_service_data = {
                        "client": client_id,
                        "myservice": my_service_id,
                        "status": True,
                        "day": repated_day,
                    }

                    client_service_serializer = KycClientServicesManagementSerializer(
                        data=client_service_data
                    )
                    if not client_service_serializer.is_valid():
                        raise ValueError(
                            f"Validation failed for client service: {client_service_serializer.errors}"
                        )
                    client_service_serializer.save(created_by=request.user.id)
                    created_client_services.append(client_service_serializer.data)

                    for vendor_data in vendor_data_list:
                        vendor_priority_data = {
                            "client": client_id,
                            "my_service": my_service_id,
                            "vendor": vendor_data.get("vendor_id"),
                            "priority": vendor_data.get("priority"),
                        }

                        vendor_priority_serializer = KycVendorPrioritySerializer(
                            data=vendor_priority_data
                        )
                        if not vendor_priority_serializer.is_valid():
                            raise ValueError(
                                f"Validation failed for vendor priority: {vendor_priority_serializer.errors}"
                            )
                        vendor_priority_serializer.save(created_by=request.user.id)
                        created_vendor_priorities.append(vendor_priority_serializer.data)

                return Response(
                    {
                        "success": True,
                        "message": "Client services and vendor priorities created successfully.",
                        "client_services": created_client_services,
                        "vendor_priorities": created_vendor_priorities,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except ValueError as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Unexpected error occurred: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
  

class KycVendorPriorityDetail(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request, pk):
        record = KycVendorPriority.objects.filter(
            pk=pk, deleted_at__isnull=True
        ).first()
        if not record:
            return Response(
                {"success": False, "message": "Record not found."}, status=404
            )
        serializer = KycVendorPrioritySerializer(record)
        return Response({"success": True, "data": serializer.data}, status=200)

    def patch(self, request, pk):
        record = KycVendorPriority.objects.filter(
            pk=pk, deleted_at__isnull=True
        ).first()
        if not record:
            return Response(
                {"success": False, "message": "Record not found."}, status=404
            )

        serializer = KycVendorPrioritySerializer(
            record, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(updated_by=request.user.id, updated_at=timezone.now())
            return Response(
                {"success": True, "message": "Vendor priority updated successfully."},
                status=200,
            )
        return Response({"success": False, "errors": serializer.errors}, status=400)

    def delete(self, request, pk):
        record = KycVendorPriority.objects.filter(
            pk=pk, deleted_at__isnull=True
        ).first()
        if not record:
            return Response(
                {"success": False, "message": "Record not found."}, status=404
            )
        record.deleted_by = request.user.id
        record.deleted_at = timezone.now()
        record.save()
        return Response(
            {"success": True, "message": "Vendor priority deleted successfully."},
            status=200,
        )
