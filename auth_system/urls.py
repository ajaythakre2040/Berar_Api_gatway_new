from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from auth_system.views.auth_view import (
    AccountUnlockView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordConfirmView,
    ChangePasswordView,
)
from auth_system.views.menu_view import (
    MenuDetailView,
    MenuListCreateView,
)
from auth_system.views.role_permission_view import (
    RolePermissionDetailView,
    RolePermissionListCreateView,
)
from auth_system.views.department_view import (
    DepartmentListCreate,
    DepartmentDetail,
    DepartmentList,
)


from auth_system.views.role_view import RoleDetailView, RoleListCreateView, RoleList

from auth_system.views.user_view import (
    UserDetailUpdateDeleteView,
    UserListCreateView,
    UserStatusUpdateView,
)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("account-unlock/", AccountUnlockView.as_view(), name="account-unlock"),
    path(
        "reset-password-confirm/",
        ResetPasswordConfirmView.as_view(),
        name="reset-password-confirm",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("users/", UserListCreateView.as_view(), name="user-list"),
    path(
        "users/<int:id>/",
        UserDetailUpdateDeleteView.as_view(),
        name="user-detail-update-delete",
    ),
    path(
        "users/update_status/<int:id>/",
        UserStatusUpdateView.as_view(),
        name="user-status-update",
    ),
    path("menus/", MenuListCreateView.as_view(), name="menu-list-create"),
    path("menus/<int:pk>/", MenuDetailView.as_view(), name="menu-detail"),
    path("roles/", RoleListCreateView.as_view(), name="role-list-create"),
    path("roles-list/", RoleList.as_view(), name="role-permission-list"),
    path("roles/<int:pk>/", RoleDetailView.as_view(), name="role-detail"),
    path(
        "role-permissions/",
        RolePermissionListCreateView.as_view(),
        name="role-permission-list-create",
    ),
    path(
        "role-permissions/<int:role_id>/",
        RolePermissionDetailView.as_view(),
        name="role-permission-detail",
    ),
    path("department/", DepartmentListCreate.as_view(), name="department-list-create"),
    path("department/<int:pk>/", DepartmentDetail.as_view(), name="department-detail"),
    path("department-list/", DepartmentList.as_view(), name="department-list"),
]
