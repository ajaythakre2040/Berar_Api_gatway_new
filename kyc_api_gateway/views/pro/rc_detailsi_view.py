from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from kyc_api_gateway.models import (
    ClientManagement,
    ProRcDetails,
    KycVendorPriority,
    KycClientServicesManagement,
)
from kyc_api_gateway.models.pro_rc_request_log import ProRcRequestLog
from kyc_api_gateway.serializers.pro_rc_detail_serializer import ProRcDetailsSerializer
from kyc_api_gateway.services.pro.rc_handler import (
    call_rc_vendor_api,
    normalize_response,
    save_data,
)
from constant import KYC_MY_SERVICES


class ProRcAPIView(APIView):
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

        rc_number = (request.data.get("rc_number") or "").strip().upper()
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        endpoint = request.path

        user = request.user if getattr(request.user, "is_authenticated", False) else None

        if not rc_number:
            self._log_request(
                rc_number=None,
                vendor=None,
                endpoint=endpoint,
                status_code=400,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="RC number required",
                user=user,
                rc_details=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response({"success": False, "status": 400, "error": "RC number required"}, status=400)

        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client

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
            )
            return Response({"success": False, "status": 500, "error": str(e)}, status=500)

        days_ago = timezone.now() - timedelta(days=cache_days)
        cached = ProRcDetails.objects.filter(rc_number__iexact=rc_number, created_at__gte=days_ago).first()

        if cached:
            serializer = ProRcDetailsSerializer(cached)
            self._log_request(
                rc_number=rc_number,
                vendor="CACHE",
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
            )
            return Response({"success": True, "status": 200, "message": "Cached data", "data": serializer.data})

        vendors = self._get_priority_vendors(client, service_id)
        print(f"[DEBUG] Found {vendors.count()} priority vendors for client={client.id}, service_id={service_id}")

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
            )
            return Response({"success": False, "status": 403, "error": error_msg}, status=403)

        last_exception = None
        for vp in vendors:
            vendor = vp.vendor
            try:
                print(f"[DEBUG] Calling vendor {vendor.vendor_name} for RC {rc_number}")

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
                    )
                    continue
                data = None
                try:
                    if hasattr(response, "json"):
                        data = response
                    else:
                        data = response
                except Exception:
                    data = None

                normalized = normalize_response(vendor.vendor_name, data or {})
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
                    )
                    continue

                rc_obj = save_data(normalized, client.id)
                serializer = ProRcDetailsSerializer(rc_obj)

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
                )

                return Response(
                    {"success": True, "status": 200, "message": f"Data retrieved from {vendor.vendor_name}", "data": serializer.data},
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
        )
        return Response({"success": False, "status": 404, "error": "All vendors failed"}, status=404)

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
            )
            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(production_key=api_key, deleted_at__isnull=True).first()
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
                     user=None, rc_details=None, ip_address=None, user_agent=None):
        ProRcRequestLog.objects.create(
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
        )
