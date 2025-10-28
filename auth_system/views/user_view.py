from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.exceptions import NotFound

from auth_system.models.user import TblUser
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.serializers.user import TblUserSerializer
from django.db.models import Q

from auth_system.utils.pagination import CustomPagination
from rest_framework.views import APIView


class UserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTokenValid]
    serializer_class = TblUserSerializer
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        try:
            search_query = request.GET.get("search", "").strip()
            department_id = request.GET.get("department_id", "").strip()
            role_id = request.GET.get("role_id", "").strip()
            user_status = request.GET.get("status", "").strip()

            queryset = TblUser.objects.filter(deleted_at__isnull=True)

            total_users = queryset.count()
            active_users = queryset.filter(status=1).count()
            lock_users = queryset.filter(status=5).count()
            custom_users = queryset.filter(role_id__type="Custom").count()
            admin_users = queryset.filter(role_id__type="System").count()

            if search_query:
                queryset = queryset.filter(
                    Q(first_name__icontains=search_query)
                    | Q(last_name__icontains=search_query)
                )
            if department_id:
                queryset = queryset.filter(department_id=department_id)

            if role_id:
                queryset = queryset.filter(role_id=role_id)

            if user_status:
                queryset = queryset.filter(status=user_status)

            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)

            paginated_response = self.get_paginated_response(
                {
                    "counts": {
                        "total_users": total_users,
                        "active_users": active_users,
                        "lock_users": lock_users,
                        "custom_users": custom_users,
                        "admin_users": admin_users,
                    },
                    "data": serializer.data,
                }
            )

            return paginated_response

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error fetching user list: {str(e)}",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(created_by=request.user.id)
            return Response(
                {
                    "success": True,
                    "message": "User created successfully.",
                    "status_code": status.HTTP_201_CREATED,
                    "data": TblUserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "User creation failed.",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TblUser.objects.filter(deleted_at__isnull=True)
    serializer_class = TblUserSerializer
    lookup_field = "id"

    def get_object(self):
        try:
            return TblUser.objects.get(id=self.kwargs["id"], deleted_at__isnull=True)
        except TblUser.DoesNotExist:
            raise NotFound(detail="User not found.", code=status.HTTP_404_NOT_FOUND)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "success": True,
                "message": "User details fetched successfully.",
                "status_code": status.HTTP_200_OK,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            instance.updated_by = request.user.id
            instance.updated_at = timezone.now()
            self.perform_update(serializer)
            return Response(
                {
                    "success": True,
                    "message": "User updated successfully.",
                    "status_code": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = timezone.now()
        instance.deleted_by = request.user.id
        instance.save()
        return Response(
            {
                "success": True,
                "message": "User deleted successfully.",
                "status_code": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class UserStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def patch(self, request, id, *args, **kwargs):
        try:
            user = TblUser.objects.get(id=id, deleted_at__isnull=True)
        except TblUser.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "User not found.",
                    "status_code": status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")
        if new_status is None:
            return Response(
                {
                    "success": False,
                    "message": "Status field is required.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.status = new_status
        user.updated_by = request.user.id
        user.updated_at = timezone.now()
        user.save()

        serializer = TblUserSerializer(user)
        return Response(
            {
                "success": True,
                "message": "User status updated successfully.",
                "status_code": status.HTTP_200_OK,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
