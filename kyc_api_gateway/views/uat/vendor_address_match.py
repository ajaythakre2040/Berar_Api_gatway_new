from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from kyc_api_gateway.models.uat_address_details import UatAddressMatch
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from kyc_api_gateway.serializers.uat_address_match_serializer import (
    UatAddressMatchSerializer,
)
from kyc_api_gateway.services.uat.address_handler import (
    call_dynamic_vendor_api,
    save_address_match,
    normalize_vendor_response,
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_address_log import UatAddressMatchRequestLog
import re
from kyc_api_gateway.utils.sanitizer import sanitize_input


class VendorUatAddressDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    # @staticmethod
    # def sanitize_input(value):
    #     if not value:
    #         return value
    #     value = value.strip()

    #     clean_value = re.sub(r"<.*?>", "", value)

    #     if re.search(
    #         r"(script|alert|onerror|onload|<|>|javascript:)", clean_value, re.IGNORECASE
    #     ):
    #         raise ValueError("Invalid characters detected in input.")

    #     return clean_value

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def _log_request(
        self,
        address1,
        address2,
        vendor_name,
        endpoint,
        status_code,
        status,
        request_payload=None,
        response_payload=None,
        error_message=None,
        user=None,
        match_obj=None,
        ip_address=None,
        user_agent=None,
    ):
        if not isinstance(status_code, int):
            raise ValueError(f"status_code must be an integer, got {status_code!r}")

        UatAddressMatchRequestLog.objects.create(
            address1=address1,
            address2=address2,
            vendor=vendor_name,
            endpoint=endpoint,
            status_code=status_code,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload,
            error_message=error_message,
            user=user if user and getattr(user, "is_authenticated", False) else None,
            address_match=match_obj,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def post(self, request):
        url = request.data.get("url")
        address1 = sanitize_input(request.data.get("address1"))
        address2 = sanitize_input(request.data.get("address2"))
        vendor = request.data.get("vendor", "Unknown Vendor").strip()
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        user = request.user if request.user.is_authenticated else None

        if not address1 or address1.strip() == "":
            missing = []
            if not address1 or address1.strip() == "":
                missing.append("address1")

        if not address2 or address2.strip() == "":
            missing = []
            if not address2 or address2.strip() == "":
                missing.append("address2")

        if not url:
            return Response(
                {"success": False, "message": "Missing required field: url"}, status=400
            )

        response = None

        try:

            response = call_dynamic_vendor_api(url, request.data)
            if response and isinstance(response, dict) and response.get("http_error"):

                error_message = response.get("error_message") or "Vendor API Error"
                vendor_message = response.get("vendor_response", {}).get(
                    "message", "Unknown error"
                )
                vendor_status_code = response.get("vendor_response", {}).get(
                    "status_code", 400
                )

                self._log_request(
                    address1=None,
                    address2=None,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=vendor_status_code,
                    status="fail",
                    request_payload=request.data,
                    response_payload=None,
                    error_message=error_message,
                    user=None,
                    match_obj=None,
                    ip_address=None,
                    user_agent=None,
                )

                return Response(
                    {
                        "success": False,
                        "status_code": vendor_status_code,
                        "message": vendor_message,
                        "error_details": error_message,
                    },
                    status=vendor_status_code,
                )

            data = response or {}
            normalized = normalize_vendor_response(vendor, data, request.data)
            if not normalized:
                self._log_request(
                    address1=address1,
                    address2=address2,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=502,
                    status="fail",
                    request_payload=request.data,
                    response_payload=data,
                    error_message=error_message,
                    user=user,
                    match_obj=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return Response(
                    {"success": False, "message": "No valid data returned"}, status=200
                )

            if not user:
                return Response(
                    {"success": False, "message": "No authenticated user found"},
                    status=401,
                )

            with transaction.atomic():
                address_obj = save_address_match(normalized, created_by=user.id)
                if not address_obj or not address_obj.id:
                    raise ValueError("Failed to save bill data")

                serializer = UatAddressMatchSerializer(address_obj)

                self._log_request(
                    address1=address1,
                    address2=address2,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    error_message=None,
                    user=user,
                    match_obj=address_obj,
                    ip_address=ip_address,
                    user_agent=user_agent,
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
            error_message = str(e)

            self._log_request(
                address1=address1,
                address2=address2,
                vendor_name=vendor,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_message,
                user=user,
                match_obj=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return Response({"success": False, "message": error_message}, status=500)
