from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from constant import STATUS_ACTIVE
from kyc_api_gateway.models.api_management import ApiManagement
from kyc_api_gateway.models.vendor_management import VendorManagement
from kyc_api_gateway.serializers.vendor_management_serializer import (
    VendorManagementSerializer,
)
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination
from django.db.models import Q


class VendorManagementListCreate(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()
        vendors = VendorManagement.objects.filter(deleted_at__isnull=True)

        total_vendor = vendors.count()
        total_active_vendor = vendors.filter(status=True).count()  

        if search_query:
            vendors = vendors.filter(
                Q(vendor_name__icontains=search_query)
                | Q(header_key_name__icontains=search_query)
                | Q(uat_base_url__icontains=search_query)
                | Q(prod_base_url__icontains=search_query)
                | Q(contact_email__icontains=search_query)
                | Q(contact_phone__icontains=search_query)
            )

        vendors = vendors.order_by("id")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(vendors, request)
        serializer = VendorManagementSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Vendor list retrieved successfully.",
                "total_vendor": total_vendor,
                "total_active_vendor": total_active_vendor,
            },
        )

    def post(self, request):
        serializer = VendorManagementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user.id)
            return Response(
                {"success": True, "message": "Vendor created successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create vendor.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class VendorManagementDetail(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request, pk):
        vendor = get_object_or_404(VendorManagement, pk=pk, deleted_at__isnull=True)
        serializer = VendorManagementSerializer(vendor)
        return Response(
            {
                "success": True,
                "message": "Vendor retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        vendor = get_object_or_404(VendorManagement, pk=pk, deleted_at__isnull=True)
        serializer = VendorManagementSerializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user.id, updated_at=timezone.now())
            return Response(
                {"success": True, "message": "Vendor updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to update vendor.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        vendor = get_object_or_404(VendorManagement, pk=pk, deleted_at__isnull=True)
        vendor.deleted_at = timezone.now()
        vendor.deleted_by = request.user.id
        vendor.save()
        return Response(
            {"success": True, "message": "Vendor deleted successfully."},
            status=status.HTTP_200_OK,
        )


class VendorNameList(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        apis = (
            VendorManagement.objects.filter(deleted_at__isnull=True)
            .order_by("id")
            .values("id", "vendor_name")
        )
        return Response(
            {
                "success": True,
                "message": "API list retrieved successfully.",
                "data": list(apis),
            },
            status=status.HTTP_200_OK,
        )


class VendorUrlList(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        vendor_id = request.query_params.get("vendor_id")
        url_type = request.query_params.get("url_type")  
        if not vendor_id or not url_type:
            return Response(
                {"success": False, "message": "vendor_id and url_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            vendor = VendorManagement.objects.values(
                "id",
                "vendor_name",
                "header_key_name",
                "uat_base_url",
                "uat_api_key",
                "prod_base_url",
                "prod_api_key",
            ).get(id=vendor_id, deleted_at__isnull=True)
        except VendorManagement.DoesNotExist:
            return Response(
                {"success": False, "message": "Vendor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        url_type = url_type.upper()
        if url_type == "UAT":
            base_url = vendor["uat_base_url"]
            vendor_details = {
                "id": vendor["id"],
                "vendor_name": vendor["vendor_name"],
                "header_key_name": vendor["header_key_name"],
                "uat_base_url": vendor["uat_base_url"],
                "api_key": vendor["uat_api_key"],
            }
        elif url_type == "PRODUCTION":
            base_url = vendor["prod_base_url"]
            vendor_details = {
                "id": vendor["id"],
                "vendor_name": vendor["vendor_name"],
                "header_key_name": vendor["header_key_name"],
                "prod_base_url": vendor["prod_base_url"],
                "api_key": vendor["prod_api_key"],
            }
        else:
            return Response(
                {
                    "success": False,
                    "message": "Invalid url_type. Allowed: UAT or Production",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        endpoints_queryset = ApiManagement.objects.filter(
            deleted_at__isnull=True, vendor_id=vendor_id
        ).values("endpoint_path", "api_name")
        endpoints = [
            {"api_name": item["api_name"], "url": f"{base_url}{item['endpoint_path']}"}
            for item in endpoints_queryset
        ]
        return Response(
            {
                "success": True,
                "message": "Vendor details fetched successfully",
                "data": {
                    "vendor_details": vendor_details,
                    "selected_url_type": url_type,
                    "endpoints": endpoints,
                },
            },
            status=status.HTTP_200_OK,
        )
