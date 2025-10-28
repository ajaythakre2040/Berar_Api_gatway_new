from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.utils import timezone
from django.db import IntegrityError


from auth_system.models.menus import Menu
from auth_system.serializers.menus_serializer import MenuSerializer
from auth_system.utils.pagination import CustomPagination
from auth_system.permissions.token_valid import IsTokenValid
from django.db.models import Q


class MenuListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get(self, request):
        search_query = request.GET.get("search", "") 
        menus = Menu.objects.filter(deleted_at__isnull=True)

        if search_query:
            menus = menus.filter(
                Q(menu_name__icontains=search_query)
                | Q(menu_code__icontains=search_query)
               
            )

        menus = menus.order_by("id")
        paginator = CustomPagination()
        page = paginator.paginate_queryset(menus, request)
        serializer = MenuSerializer(page, many=True)

        return paginator.get_custom_paginated_response(
            data=serializer.data,
            extra_fields={
                "success": True,
                "message": "Menus retrieved successfully.",
            },
        )

    def post(self, request):
        serializer = MenuSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(created_by=request.user.id)
                return Response(
                    {
                        "success": True,
                        "message": "Menu created successfully.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError as e:
                return Response(
                    {
                        "success": False,
                        "message": "Menu creation failed due to duplicate 'menu_name' or 'menu_code'.",
                        "errors": str(e),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {
                        "success": False,
                        "message": "An unexpected error occurred during menu creation.",
                        "errors": str(e),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(
            {
                "success": False,
                "message": "Failed to create menu.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class MenuDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get_object(self, pk):
        try:
            return Menu.objects.get(pk=pk, deleted_at__isnull=True)
        except Menu.DoesNotExist:
            raise NotFound(detail=f"Menu with id {pk} not found.")

    def get(self, request, pk):
        menu = self.get_object(pk)
        serializer = MenuSerializer(menu)
        return Response(
            {
                "success": True,
                "message": "Menu retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        menu = self.get_object(pk)
        serializer = MenuSerializer(menu, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save(updated_by=request.user.id, updated_at=timezone.now())
                return Response(
                    {
                        "success": True,
                        "message": "Menu updated successfully.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            except IntegrityError as e:
                return Response(
                    {
                        "success": False,
                        "message": "Update failed due to duplicate 'menu_name' or 'menu_code'.",
                        "errors": str(e),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {
                        "success": False,
                        "message": "An unexpected error occurred during menu update.",
                        "errors": str(e),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(
            {
                "success": False,
                "message": "Failed to update menu.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        menu = self.get_object(pk)
        menu.deleted_at = timezone.now()
        menu.deleted_by = request.user.id
        menu.save()
        return Response(
            {
                "success": True,
                "message": "Menu deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )




