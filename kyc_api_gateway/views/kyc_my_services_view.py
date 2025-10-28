from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination
from django.db.models import Q

from kyc_api_gateway.models.kyc_my_services import KycMyServices
from kyc_api_gateway.serializers.kyc_my_services_serializer import KycMyServicesSerializer


class KycMyServicesListCreate(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()

        services = KycMyServices.objects.filter(deleted_at__isnull=True)
        total_services = services.count()

        if search_query:
            services = services.filter(
                Q(name__icontains=search_query)
                | Q(uat_url__icontains=search_query)
                | Q(prod_url__icontains=search_query)
            )

        services = services.order_by("id")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(services, request)
        serializer = KycMyServicesSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Services list retrieved successfully.",
                "total_services": total_services,
            },
        )

    def post(self, request):
        serializer = KycMyServicesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user.id)
            return Response(
                {
                    "success": True,
                    "message": "Service created successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create service.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class KycMyServicesDetail(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request, pk):
        service = get_object_or_404(KycMyServices, pk=pk, deleted_at__isnull=True)
        serializer = KycMyServicesSerializer(service)
        return Response(
            {
                "success": True,
                "message": "Service retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        service = get_object_or_404(KycMyServices, pk=pk, deleted_at__isnull=True)
        serializer = KycMyServicesSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user.id, updated_at=timezone.now())
            return Response(
                {"success": True, "message": "Service updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to update service.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        service = get_object_or_404(KycMyServices, pk=pk, deleted_at__isnull=True)
        service.deleted_at = timezone.now()
        service.deleted_by = request.user.id
        service.save()
        return Response(
            {"success": True, "message": "Service deleted successfully."},
            status=status.HTTP_200_OK,
        )
    


class KycMyServicesNameList(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        try:
            services = (
                KycMyServices.objects.filter(deleted_at__isnull=True)
                .order_by("id")
                .values("id", "name")
            )

            if not services.exists():
                return Response(
                    {
                        "success": False,
                        "message": "No services found. Please add data first.",
                        "data": [],
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "success": True,
                    "message": "Service name list retrieved successfully.",
                    "data": list(services),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "An error occurred while fetching the service name list.",
                    "error_detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

