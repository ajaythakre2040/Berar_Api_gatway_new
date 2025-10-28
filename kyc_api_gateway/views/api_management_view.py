from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from auth_system.permissions.token_valid import IsTokenValid
from kyc_api_gateway.models.api_management import ApiManagement
from kyc_api_gateway.serializers.api_management_serializer import (
    ApiManagementSerializer,
)
from auth_system.utils.pagination import CustomPagination


class ApiManagementListCreate(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()
        apis = ApiManagement.objects.filter(deleted_at__isnull=True)

        if search_query:
            apis = apis.filter(
                Q(api_name__icontains=search_query)
                | Q(endpoint_path__icontains=search_query)
                | Q(http_method__icontains=search_query)
                | Q(descriptions__icontains=search_query)
            )

        apis = apis.order_by("id")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(apis, request)
        serializer = ApiManagementSerializer(page, many=True)

        total_apis = apis.count()
        enabled_apis = apis.filter(enable_api_endpoint=True).count()
        disabled_apis = apis.filter(enable_api_endpoint=False).count()

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "API list retrieved successfully.",
                "total_apis": total_apis,
                "enabled_apis": enabled_apis,
                "disabled_apis": disabled_apis,
            },
        )

    def post(self, request):
        serializer = ApiManagementSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "API created successfully.",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create API.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ApiManagementDetail(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get_object(self, pk):
        return get_object_or_404(ApiManagement, pk=pk, deleted_at__isnull=True)

    def get(self, request, pk):
        api = self.get_object(pk)
        serializer = ApiManagementSerializer(api)
        return Response(
            {
                "success": True,
                "message": "API retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        api = self.get_object(pk)
        serializer = ApiManagementSerializer(
            api, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "API updated successfully.",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to update API.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        api = self.get_object(pk)
        api.deleted_at = timezone.now()
        api.deleted_by = request.user.id
        api.save()
        return Response(
            {
                "success": True,
                "message": "API deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )


class ApiManagementList(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        apis = ApiManagement.objects.filter(deleted_at__isnull=True).order_by("id")
        serializer = ApiManagementSerializer(apis, many=True)
        return Response(
            {
                "success": True,
                "message": "API list retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
