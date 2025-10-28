from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from auth_system.models.department import Department
from auth_system.serializers.department_serializers import DepartmentSerializer
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from auth_system.utils.pagination import CustomPagination
from django.db.models import Q
from django.db import IntegrityError



class DepartmentListCreate(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "").strip()

        departments = Department.objects.filter(deleted_at__isnull=True)

        if search_query:
            departments = departments.filter(Q(name__icontains=search_query))

        departments = departments.order_by("id")

        paginator = CustomPagination()
        page = paginator.paginate_queryset(departments, request)
        serializer = DepartmentSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Departments retrieved successfully.",
            },
        )


    def post(self, request):
        name = request.data.get("name")

        if Department.objects.filter(name=name, deleted_at__isnull=True).exists():
            return Response(
                {"success": False, "message": "Department name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(created_by=request.user.id, created_at=timezone.now())
                return Response(
                    {
                        "success": True,
                        "message": "Department created successfully.",
                        # "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError as e:
                return Response(
                    {
                        "success": False,
                        "message": "Database error during department creation.",
                        "errors": str(e),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "success": False,
                "message": "Invalid department data.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class DepartmentDetail(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request, pk):
        department = get_object_or_404(Department, pk=pk, deleted_at__isnull=True)
        serializer = DepartmentSerializer(department)
        return Response(
            {
                "success": True,
                "message": "Department retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        department = get_object_or_404(Department, pk=pk, deleted_at__isnull=True)
        name = request.data.get("name")

        if (
            name
            and Department.objects.filter(name=name, deleted_at__isnull=True)
            .exclude(id=pk)
            .exists()
        ):
            return Response(
                {"success": False, "message": "Department name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user.id, updated_at=timezone.now())
            return Response(
                {"success": True, "message": "Department updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Failed to update department.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        department = get_object_or_404(Department, pk=pk, deleted_at__isnull=True)
        department.deleted_at = timezone.now()
        department.deleted_by = request.user.id
        department.save()
        return Response(
            {"success": True, "message": "Department deleted successfully."},
            status=status.HTTP_200_OK,
        )


class DepartmentList(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        try:
            departments = Department.objects.filter(deleted_at__isnull=True).order_by("id")
            serializer = DepartmentSerializer(departments, many=True)

            return Response(
                {
                    "success": True,
                    "message": "All departments retrieved successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Failed to fetch departments.",
                    "errors": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
