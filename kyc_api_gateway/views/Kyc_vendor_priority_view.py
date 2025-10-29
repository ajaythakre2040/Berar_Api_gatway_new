from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from kyc_api_gateway.models import KycVendorPriority
from kyc_api_gateway.serializers.Kyc_vendor_priority_serializer import (
    KycVendorPrioritySerializer,
)
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination


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

    # def post(self, request):

    #     serializer = KycVendorPrioritySerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save(created_by=request.user.id)
    #         return Response(
    #             {"success": True, "message": "Vendor priority created successfully."},
    #             status=status.HTTP_201_CREATED,
    #         )
    #     return Response(
    #         {
    #             "success": False,
    #             "message": "Failed to create vendor priority.",
    #             "errors": serializer.errors,
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    def post(self, request):
        client_id = request.data.get("client")
        service_data_list = request.data.get("my_service_data", [])

        if not client_id or not service_data_list:
            return Response(
                {
                    "success": False,
                    "message": "Missing 'client' or 'my_service_data' in request.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_records = []

        try:
            for service_data in service_data_list:
                my_service_id = service_data.get("my_service")
                vendor_data_list = service_data.get("vendor_data", [])

                if not my_service_id or not vendor_data_list:
                    return Response(
                        {
                            "success": False,
                            "message": "Missing 'my_service' or 'vendor_data' in one of the entries.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for vendor_item in vendor_data_list:
                    vendor_id = vendor_item.get("vendor")
                    priority = vendor_item.get("priority")

                    if not vendor_id or priority is None:
                        return Response(
                            {
                                "success": False,
                                "message": "Each vendor entry must include 'vendor' and 'priority'.",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    data = {
                        "client": client_id,
                        "my_service": my_service_id,
                        "vendor": vendor_id,
                        "priority": priority,
                    }

                    serializer = KycVendorPrioritySerializer(data=data)
                    if serializer.is_valid():
                        serializer.save(created_by=request.user.id)
                        created_records.append(serializer.data)
                    else:
                        return Response(
                            {
                                "success": False,
                                "message": "Validation failed.",
                                "errors": serializer.errors,
                                "invalid_data": data,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            return Response(
                {
                    "success": True,
                    "message": "Vendor priorities created successfully.",
                    "data": created_records,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"success": False, "message": f"Error: {str(e)}"},
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
