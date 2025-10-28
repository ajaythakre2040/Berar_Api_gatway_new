from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db import transaction
from auth_system.models.role_permission import RolePermission
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.serializers.role_permission_serializer import RolePermissionSerializer
from auth_system.utils.pagination import CustomPagination


class RolePermissionListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        permissions = RolePermission.objects.filter(deleted_at__isnull=True).order_by(
            "id"
        )
        paginator = CustomPagination()
        page = paginator.paginate_queryset(permissions, request)
        serializer = RolePermissionSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Role permissions retrieved successfully.",
            },
        )

    def post(self, request):
        serializer = RolePermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user.id)
            return Response(
                {
                    "success": True,
                    "message": "Role permission created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to create role permission.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class RolePermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get_role_permissions(self, role_id):
        perms = RolePermission.objects.filter(role_id=role_id, deleted_at__isnull=True)
        if not perms.exists():
            raise NotFound(f"No permissions found for role ID {role_id}.")
        return perms

    def get(self, request, role_id):
        perms = self.get_role_permissions(role_id)
        serializer = RolePermissionSerializer(perms, many=True)
        return Response(
            {
                "success": True,
                "message": f"Permissions retrieved for role ID {role_id}.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, role_id):
        perms = self.get_role_permissions(role_id)
        perm_map = {p.menu_id_id: p for p in perms}
        data = request.data if isinstance(request.data, list) else [request.data]
        updated = []

        with transaction.atomic():
            for item in data:
                perm = perm_map.get(item.get("menu_id"))
                if not perm:
                    continue
                serializer = RolePermissionSerializer(perm, data=item, partial=True)
                if serializer.is_valid():
                    serializer.save(
                        updated_at=timezone.now(), updated_by=request.user.id
                    )
                    updated.append(serializer.data)
                else:
                    return Response(
                        {
                            "success": False,
                            "message": "Failed to update permission.",
                            "errors": serializer.errors,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        return Response(
            {
                "success": True,
                "message": f"Permissions updated successfully for role ID {role_id}.",
                "data": updated,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, role_id):
        count = RolePermission.objects.filter(
            role_id=role_id, deleted_at__isnull=True
        ).update(deleted_at=timezone.now(), deleted_by=request.user.id)
        if count == 0:
            return Response(
                {
                    "success": False,
                    "message": f"No active permissions found to delete for role ID {role_id}.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "message": f"Deleted {count} permissions for role ID {role_id}.",
            },
            status=status.HTTP_200_OK,
        )


