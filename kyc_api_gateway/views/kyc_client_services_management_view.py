from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination

from kyc_api_gateway.models.kyc_client_services_management import KycClientServicesManagement
from kyc_api_gateway.serializers.kyc_client_services_management_serializer import (
    KycClientServicesManagementSerializer,
)


class KycClientServicesListCreate(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()

        services = KycClientServicesManagement.objects.filter(deleted_at__isnull=True)
        total_services = services.count()
        total_active = services.filter(status=True).count()

        if search_query:
            services = services.filter(
                Q(client__company_name__icontains=search_query)
                | Q(myservice__name__icontains=search_query)
                | Q(priority__icontains=search_query)
            )

        services = services.select_related("client", "myservice").order_by("priority")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(services, request)
        serializer = KycClientServicesManagementSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Client services list retrieved successfully.",
                "total_services": total_services,
                "total_active": total_active,
            },
        )

    def post(self, request):
        serializer = KycClientServicesManagementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user.id)
            return Response(
                {
                    "success": True,
                    "message": "Client service mapping created successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create client service mapping.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class KycClientServicesDetail(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request, pk):
        service_map = get_object_or_404(
            KycClientServicesManagement, pk=pk, deleted_at__isnull=True
        )
        serializer = KycClientServicesManagementSerializer(service_map)
        return Response(
            {
                "success": True,
                "message": "Client service mapping retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        service_map = get_object_or_404(
            KycClientServicesManagement, pk=pk, deleted_at__isnull=True
        )
        serializer = KycClientServicesManagementSerializer(
            service_map, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(updated_by=request.user.id, updated_at=timezone.now())
            return Response(
                {"success": True, "message": "Client service mapping updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to update client service mapping.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        service_map = get_object_or_404(
            KycClientServicesManagement, pk=pk, deleted_at__isnull=True
        )
        service_map.deleted_at = timezone.now()
        service_map.deleted_by = request.user.id
        service_map.save()
        return Response(
            {"success": True, "message": "Client service mapping deleted successfully."},
            status=status.HTTP_200_OK,
        )
