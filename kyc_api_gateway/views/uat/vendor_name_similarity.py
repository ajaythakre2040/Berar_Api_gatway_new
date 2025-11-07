from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from kyc_api_gateway.models.uat_name_details import UatNameMatch
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from kyc_api_gateway.serializers.uat_name_match_serializer import UatNameMatchSerializer
from kyc_api_gateway.services.uat.name_handler import (
    call_dynamic_vendor_api,
    save_name_match_uat,
    normalize_vendor_response,
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_name_request_log import UatNameMatchRequestLog


class VendorUatNameDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def _log_request(
        self, 
        name1, 
        name2, 
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
        user_agent=None
    ):

         if not isinstance(status_code, int):
            raise ValueError(f"status_code must be an integer, got {status_code!r}")
         
         UatNameMatchRequestLog.objects.create(
                name_1=name1,
                name_2=name2,
                vendor=vendor_name,
                endpoint=endpoint,
                status_code=status_code,
                status=status,
                request_payload=request_payload,
                response_payload=response_payload,
                error_message=error_message,
                user=user if user and user.is_authenticated else None,
                name_match=match_obj,
                ip_address=ip_address,
                user_agent=user_agent,
         )

    def post(self, request):
        url = request.data.get("url")
        name1 = request.data.get("name_1").strip()
        name2 = request.data.get("name_2").strip()
        vendor = request.data.get("vendor", "Unknown Vendor").strip()
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        user = request.user if request.user.is_authenticated else None
        
        # ✅ Basic Validation
        
        if not name1 or not name2 or name1.strip() == "" or name2.strip() == "":
            missing = []
            if not name1 or name1.strip() == "":
                missing.append("name_1")
            if not name2 or name2.strip() == "":
                missing.append("name_2")

        response = None  # Important initialization

        try:
            # Call vendor API
            response = call_dynamic_vendor_api(url, request.data)

            # ✅ Vendor error response handling
            if response and isinstance(response, dict) and response.get("http_error"):
                error_message = response.get("error_message") or "Vendor API Error"

                self._log_request(
                    name1=name1,
                    name2=name2,
                    vendor_name=None,
                    endpoint=request.path,
                    status_code=403,
                    status="fail",
                    request_payload=request.data,
                    response_payload=None,
                    error_message=error_message,
                    user=None,
                    match_obj=None,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                return Response(
                    {
                        "success": False,
                        "status": response.get("status_code"),
                        "message": error_message,
                        "vendor_response": response.get("vendor_response"),
                    },
                    status=response.get("status_code") or 400,
                )

            data = response or {}
            normalized = normalize_vendor_response(vendor, data)
            if not normalized:
                self._log_request(
                    name1=name1,
                    name2=name2,
                    vendor_name=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=502,
                    status="fail",
                    request_payload=request.data,
                    response_payload=data,
                    error_message=error_message,
                    user=None,
                    match_obj=None,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return Response({"success": False, "message": "No valid data returned"}, status=200)

            if not user:
                return Response({"success": False, "message": "No authenticated user found"}, status=401)

            # ✅ Save data
            with transaction.atomic():
                name_obj = save_name_match_uat(normalized, created_by=user.id)
                if not name_obj or not name_obj.id:
                    raise ValueError("Failed to save bill data")

                serializer = UatNameMatchSerializer(name_obj)

                self._log_request(
                    name1=name1,
                    name2=name2,
                    vendor_name="cached",
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    error_message=None,
                    user=None,
                    match_obj=name_obj,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

            return Response(
                {"success": True, "message": "Data successfully fetched", "data": serializer.data},
                status=200
            )

        except Exception as e:
            error_message = str(e)

            self._log_request(
                name1=name1,
                name2=name2,
                vendor_name=vendor.vendor_name,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_message,
                user=None,
                match_obj=None,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return Response({"success": False, "message": error_message}, status=500)
