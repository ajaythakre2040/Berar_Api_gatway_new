from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from constant import STATUS_ACTIVE
from kyc_api_gateway.models.client_management import ClientManagement
from kyc_api_gateway.serializers.client_management_serializer import (
    ClientManagementSerializer,
)
from rest_framework.permissions import  AllowAny
from kyc_api_gateway.models.api_management import ApiManagement
from auth_system.utils.pagination import CustomPagination
from django.db.models import Q
from kyc_api_gateway.utils.key_generator import generate_secure_token
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid


class ClientManagementListCreate(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()

        clients = ClientManagement.objects.filter(deleted_at__isnull=True)
        total_client = clients.count()
        total_active_client = clients.filter(status=STATUS_ACTIVE).count()
        total_api = ApiManagement.objects.filter(deleted_at__isnull=True).count()

        if search_query:
            clients = clients.filter(
                Q(company_name__icontains=search_query)
                | Q(registration_number__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(phone__icontains=search_query)
            )

        clients = clients.order_by("id")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(clients, request)
        serializer = ClientManagementSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Client list retrieved successfully.",
                "total_client": total_client,
                "total_active_client": total_active_client,
                "total_api": total_api,
            },
        )

    def post(self, request):
        serializer = ClientManagementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user.id)
            return Response(
                {
                    "success": True,
                    "message": "Client created successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create client.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ClientManagementDetail(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        client = get_object_or_404(ClientManagement, pk=pk, deleted_at__isnull=True)
        serializer = ClientManagementSerializer(client)
        return Response(
            {
                "success": True,
                "message": "Client retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        client = get_object_or_404(ClientManagement, pk=pk, deleted_at__isnull=True)
        serializer = ClientManagementSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user.id, updated_at=timezone.now())
            return Response(
                {"success": True, "message": "Client updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to update client.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        client = get_object_or_404(ClientManagement, pk=pk, deleted_at__isnull=True)
        client.deleted_at = timezone.now()
        client.deleted_by = request.user.id
        client.save()
        return Response(
            {"success": True, "message": "Client deleted successfully."},
            status=status.HTTP_200_OK,
        )

class ClientManagementChangeKey(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, pk):
        client = get_object_or_404(ClientManagement, pk=pk, deleted_at__isnull=True)

        if client.status != 1:
            return Response(
                {
                    "success": False,
                    "message": "Client is not active. Key update not allowed."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        key_type = request.data.get("key_type")
        if key_type not in ["uat_key", "production_key"]:

            return Response(
                {
                    "success": False,
                    "message": "Invalid key type. Use 'uat_key' or 'production key'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_token = generate_secure_token()

        setattr(client, key_type, new_token)

        client.updated_by = request.user.id if request.user else None
        client.updated_at = timezone.now()
        client.save()

        return Response(
            {
                "success": True,
                "message": f"{key_type} updated successfully.",
                "key_type": key_type,
                "new_key": new_token,
            },
            status=status.HTTP_200_OK,
        )


