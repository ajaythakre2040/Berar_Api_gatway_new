from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from kyc_api_gateway.models.uat_driving_license import UatDrivingLicense
from kyc_api_gateway.serializers.uat_driving_serializer import (
    UatDrivingLicenseSerializer,
)
from kyc_api_gateway.services.uat.driving_license_handler import (
    save_uat,
    normalize_vendor_response,
    call_dynamic_vendor_api,
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_driving_license_log import UatDrivingLicenseRequestLog
from auth_system.permissions.token_valid import IsTokenValid
from rest_framework.permissions import IsAuthenticated


class VendorUatDrivingDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def _log_request(
        self,
        request_id,
        dl_number=None,
        name=None,
        vendor=None,
        endpoint=None,
        status_code=500,
        status="fail",
        request_payload=None,
        response_payload=None,
        error_message=None,
        dl_obj=None,
        user=None,
        ip_address=None,
        user_agent=None,
    ):

        if not isinstance(status_code, int):
            status_code = 500
        UatDrivingLicenseRequestLog.objects.create(
            dl_number=dl_number,
            driving_license=dl_obj,
            request_id=request_id,
            name=name,
            vendor=vendor,
            endpoint=endpoint,
            status_code=status_code,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload,
            error_message=error_message,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def post(self, request):
        url = request.data.get("url")
        dlNo = (request.data.get("license_no") or "dlNo").strip().upper()
        dob = request.data.get("dob")
        vendor = request.data.get("vendor", "Unknown Vendor")
        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        user = request.user if request.user.is_authenticated else None

        if not dlNo or not dob:
            missing = []
            if not dlNo:
                missing.append("license_no")
            if not dob:
                missing.append("dob")
            error_msg = f"Missing required fields: {', '.join(missing)}"

            return Response(
                {"success": False, "status": 400, "error": error_msg}, status=400
            )

        try:

            response = call_dynamic_vendor_api(url, request.data)

            if response and isinstance(response, dict) and response.get("http_error"):
                self._log_request(
                    dl_number=dlNo,
                    request_id=None,
                    vendor=vendor,
                    endpoint=request.path,
                    status_code=response.get("status_code") or 500,
                    status="fail",
                    request_payload=request.data,
                    response_payload=response.get("vendor_response"),
                    error_message=response.get("error_message"),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user=user,
                )
                return Response(response, status=response.get("status_code") or 500)

            data = response or {}
            normalized = normalize_vendor_response(vendor, data)

            if not normalized:
                self._log_request(
                    dl_number=dlNo,
                    request_id=None,
                    vendor=vendor,
                    endpoint=request.path,
                    status_code=204,
                    status="fail",
                    request_payload=request.data,
                    response_payload=response,
                    error_message="No valid data returned",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user=user,
                )
                return Response(
                    {"success": False, "message": "No valid data returned"},
                    status=200,
                )

            dlNo_obj = save_uat(normalized, vendor_name=vendor, created_by=user.id)
            if not dlNo_obj.id:
                raise ValueError("Failed to save dlNo_obj.")

            serializer = UatDrivingLicenseSerializer(dlNo_obj)

            self._log_request(
                dl_number=dlNo,
                request_id=dlNo_obj.request_id,
                vendor=vendor,
                endpoint=request.path,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                error_message=None,
                ip_address=ip_address,
                user_agent=user_agent,
                dl_obj=dlNo_obj,
                user=user,
            )

            return Response(
                {
                    "success": True,
                    "message": "Data successfully fetched",
                    "data": serializer.data,
                },
                status=200,
            )
        except Exception as e:

            self._log_request(
                dl_number=dlNo,
                vendor=vendor,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
                user=user,
            )
            return Response(
                {"success": False, "message": "Internal server error"}, status=500
            )
