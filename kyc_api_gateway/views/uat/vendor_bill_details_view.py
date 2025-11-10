from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from kyc_api_gateway.models.uat_bill_details import UatElectricityBill
from kyc_api_gateway.serializers.uat_bill_details_serializer import (
    UatElectricityBillSerializer,
)
from kyc_api_gateway.services.uat.bill_handler import (
    call_dynamic_vendor_api,
    save_bill_data,
    normalize_vendor_response,
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_bill_request_log import UatBillRequestLog
from kyc_api_gateway.utils.sanitizer import sanitize_input


class VendorUatBillDetailsAPIView(APIView):
    permission_classes = []

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def _log_request(
        self,
        customer_id,
        service_provider,
        vendor_name,
        endpoint,
        status_code,
        status,
        request_payload=None,
        response_payload=None,
        error_message=None,
        user=None,
        bill_details=None,
        ip_address=None,
        user_agent=None,
    ):
        if not isinstance(status_code, int):
            raise ValueError(f"status_code must be an integer, got {status_code!r}")
        UatBillRequestLog.objects.create(
            customer_id=customer_id,
            operator_code=service_provider,
            bill_details=bill_details,
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
            consumer_id = ((sanitize_input(request.data.get("consumer_id")) or "").strip().upper())
            service_provider = sanitize_input(request.data.get("service_provider"))
            
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
        
        if not consumer_id:
            return Response(
                {"success": False, "message": "Missing required field: consumer_id"},
                status=400,
            )
        if not service_provider:
            return Response(
                {"success": False, "message": "Missing required field: service_provider"},
                status=400,
            )
        if not url:
            return Response(
                {"success": False, "message": "Missing required field: url"}, status=400
            )
        response = None
        
        try:
            response = call_dynamic_vendor_api(url, request.data)
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
                    customer_id=consumer_id,
                    service_provider=service_provider,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=vendor_status_code,
                    status="fail",
                    request_payload=request.data,
                    response_payload=vendor_resp,
                    error_message=error_message,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
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
                    customer_id=consumer_id,
                    service_provider=service_provider,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=204,
                    status="fail",
                    request_payload=request.data,
                    response_payload=data,
                    error_message="No valid data returned",
                    user=user,
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
                bill_obj = save_bill_data(normalized, created_by=user.id)
                if not bill_obj or not bill_obj.id:
                    raise ValueError("Failed to save bill data")
                serializer = UatElectricityBillSerializer(bill_obj)
                self._log_request(
                    customer_id=consumer_id,
                    service_provider=service_provider,
                    vendor_name=vendor,
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    user=user,
                    bill_details=bill_obj,
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
                customer_id=consumer_id,
                service_provider=service_provider,
                vendor_name=vendor,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=response if response else None,
                error_message=error_message,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response({"success": False, "message": error_message}, status=500)