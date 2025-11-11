from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination
from django.db.models import Q

from kyc_api_gateway.models.kyc_my_services import KycMyServices
from kyc_api_gateway.serializers.kyc_my_services_serializer import (
    KycMyServicesSerializer,
)
from client_auth.permissions.authentication import ClientJWTAuthentication
from client_auth.models.login_session import LoginSession   
from kyc_api_gateway.models import KycClientServicesManagement



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


class KycMyServicesListAll(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        services = KycMyServices.objects.filter(deleted_at__isnull=True).order_by("id")

        serializer = KycMyServicesSerializer(services, many=True)

        return Response(
            {
                "success": True,
                "message": "Services list retrieved successfully.",
                "data": serializer.data,
            },
            status=200,
        )

class KycMyClientServicesListAll(APIView):
    authentication_classes = [ClientJWTAuthentication]

    print("KycMyServicesListAll accessed")
    permission_classes = [AllowAny]  

    def get(self, request):
        user = request.user

        if not user or not hasattr(user, "id"):
            services = KycMyServices.objects.filter(deleted_at__isnull=True).order_by("id")

        else:
            client_id = user.id

            active_session = (
                LoginSession.objects.filter(client_id=client_id, is_active=True)
                .order_by("-login_at")
                .first()
            )

            if not active_session:
                return Response({
                    "success": False,
                    "message": "Session expired or not logged in. Please login again."
                }, status=401)

            if active_session.expiry_at and active_session.expiry_at < timezone.now():
                active_session.is_active = False
                active_session.save(update_fields=["is_active"])
                return Response({
                    "success": False,
                    "message": "Session expired. Please login again."
                }, status=401)

            allowed_service_ids = (
                KycClientServicesManagement.objects.filter(
                    client_id=client_id,
                    status=True,
                    deleted_at__isnull=True
                )
                .values_list("myservice_id", flat=True)
            )

            services = KycMyServices.objects.filter(
                id__in=allowed_service_ids, deleted_at__isnull=True
            ).order_by("id")

        serializer = KycMyServicesSerializer(services, many=True)

        return Response(
            {
                "success": True,
                "message": "Services list retrieved successfully.",
                "data": serializer.data,
            },
            status=200,
        )