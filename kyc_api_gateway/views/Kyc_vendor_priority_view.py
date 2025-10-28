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

    def post(self, request):

        serializer = KycVendorPrioritySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user.id)
            return Response(
                {"success": True, "message": "Vendor priority created successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create vendor priority.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
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
