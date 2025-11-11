from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from kyc_api_gateway.models.uat_voter_details import UatVoterDetail
from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid
from kyc_api_gateway.serializers.uat_voter_details_serializer import UatVoterDetailSerializer
from kyc_api_gateway.services.uat.voter_handler import (
    call_dynamic_vendor_api,
    save_voter_data,
    normalize_vendor_response,
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_voter_request_log import UatVoterRequestLog
from kyc_api_gateway.utils.sanitizer import sanitize_input


class VendorUatVoterDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTokenValid]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")
    
    def _log_request(
        self, 
        voter_id, 
        vendor_name, 
        endpoint, 
        status_code, 
        status,   
        request_payload=None, 
        response_payload=None, 
        error_message=None,
        user=None, 
        voter_obj=None, 
        ip_address=None, 
        user_agent=None
    ):

        if not isinstance(status_code, int):
            raise ValueError(f"status_code must be an integer, got {status_code!r}")

        UatVoterRequestLog.objects.create(
            voter_detail=voter_obj,
            vendor=vendor_name,
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
        try:
            voter_id = sanitize_input(request.data.get("id_number") or "").strip().upper()
            
        except ValueError as e:
            error_message = str(e)
            return Response(
                {
                    "success": False,
                    "status": 400,
                    "error": "Invalid input",
                    "message": "Your input contains invalid characters. Please try again.",
                },
                status=400,
            )
            
        url = request.data.get("url")
        vendor = request.data.get("vendor", "Unknown Vendor").strip()
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        user = request.user if request.user.is_authenticated else None
        
        if not voter_id:
            return Response(
                {"success": False, "message": "Missing required field: voter_id"},
                status=400,
            )
            
        if not url:
            return Response(
                {"success": False, "message": "Missing required field: url"}, status=400
            )
        response = None

        try:
            # Call vendor API
            response = call_dynamic_vendor_api(url, request.data)

            # ✅ Vendor error response handling
            if response and isinstance(response, dict) and response.get("http_error"):
                vendor_resp = response.get("vendor_response") or {}

                error_message = response.get("error_message") or "Vendor API Error"

                vendor_status_code = (
                    vendor_resp.get("status_code") or
                    vendor_resp.get("status") or
                    response.get("status_code") or
                    400
                )

                vendor_message = (
                    vendor_resp.get("message") or
                    vendor_resp.get("error") or
                    vendor_resp.get("error_message") or
                    error_message or
                    "Vendor API Error"
                )
                self._log_request(
                    voter_id=None,
                    vendor_name=None,
                    endpoint=request.path,
                    status_code=vendor_status_code,
                    status="fail",
                    request_payload=request.data,
                    response_payload=vendor_resp,
                    error_message=error_message,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
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
            normalized = normalize_vendor_response(vendor, data)
            if not normalized:
                self._log_request(
                    voter_id=voter_id,
                    vendor_name=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=204,
                    status="fail",
                    request_payload=request.data,
                    response_payload=getattr(response, 'text', None),
                    error_message="No valid data returned",
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return Response({"success": False, "message": "No valid data returned"}, status=200)

            if not user:
                return Response({"success": False, "message": "No authenticated user found"}, status=401)

            # ✅ Save data
            with transaction.atomic():
                voter_obj = save_voter_data(normalized, created_by=user.id)
                if not voter_obj or not voter_obj.id:
                    raise ValueError("Failed to save bill data")

                serializer = UatVoterDetailSerializer(voter_obj)

                self._log_request(
                    voter_id=voter_id,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    user=user,
                    voter_detail=voter_obj,
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
                voter_id=voter_id,
                vendor_name=vendor.vendor_name,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return Response({"success": False, "message": error_message}, status=500)
