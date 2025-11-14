from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from kyc_api_gateway.models import (
    ClientManagement,
    UatRcDetails,
    KycVendorPriority,
    KycClientServicesManagement,
)
from kyc_api_gateway.models.uat_rc_request_log import UatRcRequestLog
from kyc_api_gateway.serializers.uat_rc_detail_serializer import UatRcDetailsSerializer
from kyc_api_gateway.services.uat.rc_handler import (
    call_rc_vendor_api,
    normalize_rc_response,
    save_rc_data,
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.utils.sanitizer import sanitize_input

class RcUatAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def post(self, request):

        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client
    
        try:
            rc_number = sanitize_input(request.data.get("rc_number"))
            if rc_number:
                rc_number = rc_number.strip().upper()
        except ValueError as e:
            return Response({
                "success": False,
                "status": 400,
                "error": str(e)
            }, status=400)

        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        endpoint = request.path

        user = request.user if getattr(request.user, "is_authenticated", False) else None

        if not rc_number:
           
            return Response({"success": False, "status": 400, "error": "RC number required"}, status=400)

       
        service_name = "RC"
        service_id = KYC_MY_SERVICES.get(service_name.upper())
        if not service_id:
            error_msg = f"{service_name} service not configured"
            self._log_request(
                rc_number=rc_number,
                vendor=None,
                endpoint=endpoint,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=user,
                rc_details=None,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id if client else None,
            )
            return Response({"success": False, "status": 403, "error": error_msg}, status=403)

        try:
            cache_days = self._get_cache_days(client, service_id)
        except PermissionError as e:
            self._log_request(
                rc_number=rc_number,
                vendor=None,
                endpoint=endpoint,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=user,
                rc_details=None,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id
            )
            return Response({"success": False, "status": 403, "error": str(e)}, status=403)
        except ValueError as e:
            self._log_request(
                rc_number=rc_number,
                vendor=None,
                endpoint=endpoint,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=user,
                rc_details=None,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id
            )
            return Response({"success": False, "status": 500, "error": str(e)}, status=500)

        days_ago = timezone.now() - timedelta(days=cache_days)
        cached = UatRcDetails.objects.filter(rc_number__iexact=rc_number, created_at__gte=days_ago).first()

        if cached:
            serializer = UatRcDetailsSerializer(cached)
            self._log_request(
                rc_number=rc_number,
                vendor="cached",
                endpoint=endpoint,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                error_message=None,
                user=user,
                rc_details=cached,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id
            )

            message = (
                "Data from cache" if client.id == 1
                else "Data fetched successfully"
            )
            return Response({"success": True, "status": 200, "message": message, "data": serializer.data})

        vendors = self._get_priority_vendors(client, service_id)

        if not vendors.exists():
            error_msg = "No vendors assigned for this service"
            self._log_request(
                rc_number=rc_number,
                vendor=None,
                endpoint=endpoint,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=user,
                rc_details=None,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id
            )

            error_msg = (
                error_msg if client.id == 1
                else "Service currently not accessible"

            )
            return Response({"success": False, "status": 403, "error": error_msg}, status=403)

        last_exception = None
        for vp in vendors:
            vendor = vp.vendor
            try:
                response = call_rc_vendor_api(vendor, request.data)
               
                if response and response.get("http_error"):
                    self._log_request(
                        rc_number=rc_number,
                        vendor=vendor.vendor_name,
                        endpoint=endpoint,
                        status_code=response.get("status_code") or 500,
                        status="fail",
                        request_payload=request.data,
                        response_payload=response.get("vendor_response"),
                        error_message=response.get("error_message"),
                        user=user,
                        rc_details=None,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        created_by=client.id
                    )
                    continue
                                
                data = None
                try:
                    data = response if isinstance(response, dict) else {}
                except Exception:
                    data = None
                normalized = normalize_rc_response(vendor.vendor_name, data or {})
                if not normalized:
                    
                    self._log_request(
                        rc_number=rc_number,
                        vendor=vendor.vendor_name,
                        endpoint=endpoint,
                        status_code=204,
                        status="fail",
                        request_payload=request.data,
                        response_payload=getattr(response, "text", None),
                        error_message="No valid data returned",
                        user=user,
                        rc_details=None,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        created_by=client.id    
                    )
                    continue

                rc_obj = save_rc_data(normalized, client.id)
                serializer = UatRcDetailsSerializer(rc_obj)

                self._log_request(
                    rc_number=rc_number,
                    vendor=vendor.vendor_name,
                    endpoint=endpoint,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    error_message=None,
                    user=user,
                    rc_details=rc_obj,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=client.id
                )

                message = (
                    f"Data from {vendor.vendor_name}"
                    if client.id == 1
                    else "Data fetched successfully"
                )

                return Response(
                    {"success": True, "status": 200, "message":message, "data": serializer.data},
                    status=200
                )

            except Exception as e:
                last_exception = e
                self._log_request(
                    rc_number=rc_number,
                    vendor=vendor.vendor_name,
                    endpoint=endpoint,
                    status_code=500,
                    status="fail",
                    request_payload=request.data,
                    response_payload=None,
                    error_message=str(e),
                    user=user,
                    rc_details=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_by=client.id
                )
                continue

        if last_exception:
            pass

        self._log_request(
            rc_number=rc_number,
            vendor=None,
            endpoint=endpoint,
            status_code=404,
            status="fail",
            request_payload=request.data,
            response_payload=None,
            error_message="All vendors failed",
            user=user,
            rc_details=None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_by=client.id
        )

        final_error_message = (
            "No vendor returned valid data. All vendor requests failed."
            if client.id == 1
            else "Unable to process the request at the moment. Please try again later."
        )

        return Response({"success": False, "status": 404, "error": final_error_message}, status=404)

    def _authenticate_client(self, request):
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            self._log_request(
                rc_number=None,
                vendor=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Missing API key",
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id if client else None,
            )
            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(uat_key=api_key, deleted_at__isnull=True).first()
        if not client:
            self._log_request(
                rc_number=None,
                vendor=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Invalid API key",
                user=None,
                rc_details=None,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id if client else None,

            )
            return Response({"success": False, "status": 401, "error": "Invalid API key"}, status=401)
        return client

    def _get_cache_days(self, client, service_id):
        cs = KycClientServicesManagement.objects.filter(
            client=client,
            myservice__id=service_id,
            deleted_at__isnull=True,
        ).first()
        if not cs:
            raise ValueError(f"Cache days not configured for client={client.id}, service_id={service_id}")
        if cs.status is False:
            raise PermissionError("Service is not permitted for client")
        
        success_count = UatRcRequestLog.objects.filter(
            created_by=client.id,
            status_code__in=["200", 200],
            status__iexact="success" 
        ).count()
        
        if success_count >= cs.uat_api_limit:
           
            raise PermissionError(f"UAT API limit exceeded")
        return cs.day

    def _get_priority_vendors(self, client, service_id):
        return (
            KycVendorPriority.objects.filter(
                client=client,
                my_service_id=service_id,
                deleted_at__isnull=True,
            )
            .select_related("vendor")
            .order_by("priority")
        )

    def _log_request(self, rc_number, vendor, endpoint, status_code, status,
                     request_payload=None, response_payload=None, error_message=None,
                     user=None, rc_details=None, ip_address=None, user_agent=None, created_by=None):
        UatRcRequestLog.objects.create(
            rc_number=rc_number,
            rc_details=rc_details,
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
            created_by=created_by
        )
