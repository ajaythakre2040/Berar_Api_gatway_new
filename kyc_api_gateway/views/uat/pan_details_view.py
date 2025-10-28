from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from kyc_api_gateway.models import (
    UatPanDetails,
    ClientManagement,
    KycClientServicesManagement,
    KycVendorPriority
)
from kyc_api_gateway.serializers.uat_pan_details_serializer import UatPanDetailsSerializer
from kyc_api_gateway.services.uat.pan_handler import (
    call_vendor_api,
    save_pan_data,
    normalize_vendor_response
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_pan_request_log import UatPanRequestLog


class UatPanDetailsAPIView(APIView):
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
        pan = (request.data.get("pan") or "").strip().upper()
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        if not pan or pan.strip() == "":
            error_msg = "Missing required field: pan"
            self._log_request(
                pan_number=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=400,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response(
                {"success": False, "status": 400, "error": error_msg}, status=400
            )

        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client

        service_name = "PAN"
        service_id = KYC_MY_SERVICES.get(service_name.upper())

        if not service_id:
            error_msg = f"{service_name} service not configured"
            self._log_request(
                pan_number=pan,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response(
                {"success": False, "status": 403, "error": error_msg}, status=403
            )

        try:
            cache_days = self._get_cache_days(client, service_id)

        except PermissionError as e:

            self._log_request(
                name1=None,
                name2=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=None,
                match_obj=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 403,
                "error": str(e)   # ✅ fix here
            }, status=403)

        except ValueError as e:
            self._log_request(
                pan_number=pan,
                vendor_name=None,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response({
                "success": False,
                "status": 500,
                "error": str(e)
            }, status=500)
        
        days_ago = timezone.now() - timedelta(days=cache_days)

        cached = UatPanDetails.objects.filter(
            pan_number__iexact=pan, 
            created_at__gte=days_ago
        ).first()

        if cached:
            serializer = UatPanDetailsSerializer(cached)
            self._log_request(
                pan_number=pan,
                vendor_name="CACHE",
                endpoint=request.path,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                user=None,
                pan_details=cached,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response(
                {"success": True, "status": 200, "message": "Cached data", "data": serializer.data}
            )

        vendors = self._get_priority_vendors(client, service_id)

        print(f"[DEBUG] Found {vendors.count()} priority vendors for client={client.id}, service_id={service_id}")


        if not vendors.exists():
            error_msg = "No vendors assigned for this service"
            self._log_request(
                pan_number=pan,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response(
                {"success": False, "status": 403, "error": error_msg}, status=403
            )

        for vp in vendors:
            vendor = vp.vendor

            print(f"[DEBUG] Calling vendor {vendor.vendor_name} for PAN {pan}")
            try:
                response = call_vendor_api(vendor, request.data)
               
                if response and isinstance(response, dict) and response.get("http_error"):
                        self._log_request(
                            pan_number=pan,
                            vendor_name=vendor.vendor_name,
                            endpoint=request.path,
                            status_code=response.get("status_code") or 500,
                            status="fail",
                            request_payload=request.data,
                            response_payload=response.get("vendor_response"),
                            error_message=response.get("error_message"),
                            ip_address=ip_address,
                            user_agent=user_agent,
                        )
                        continue
                data = None
                try:
                    data = response
                except Exception:
                    pass

                normalized = normalize_vendor_response(vendor.vendor_name, data or {})
                if not normalized:
                    self._log_request(
                        pan_number=pan,
                        vendor_name=vendor.vendor_name,
                        endpoint=request.path,
                        status_code=204,
                        status="fail",
                        request_payload=request.data,
                        response_payload=getattr(response, "text", None),
                        error_message="No valid data returned",
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                    continue

                pan_obj = save_pan_data(normalized, client.id)
               
                serializer = UatPanDetailsSerializer(pan_obj)

                self._log_request(
                    pan_number=pan,
                    vendor_name=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    pan_details=pan_obj,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                return Response(
                    {
                        "success": True,
                        "status": 200,
                        "message": f"Data from {vendor.vendor_name}",
                        "data": serializer.data,
                    }
                )

            except Exception as e:
                self._log_request(
                    pan_number=pan,
                    vendor_name=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=500,
                    status="fail",
                    request_payload=request.data,
                    response_payload=None,
                    error_message=str(e),
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                continue

        return Response(
            {"success": False, "status": 404, "error": "No vendor returned valid data"},
            status=404,
        )


    def _authenticate_client(self, request):
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        api_key = request.headers.get("X-API-KEY")

        if not api_key:
            self._log_request(
                pan_number=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                error_message="Missing API key",
                request_payload=request.data,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(
            uat_key=api_key, deleted_at__isnull=True
        ).first()

        if not client:
            self._log_request(
                pan_number=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                error_message="Invalid API key",
                request_payload=request.data,
                ip_address=ip_address,
                user_agent=user_agent,
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

    def _log_request(
        self,
        pan_number,
        vendor_name,
        endpoint,
        status_code,
        status,
        request_payload=None,
        response_payload=None,
        error_message=None,
        user=None,
        pan_details=None,
        ip_address=None,
        user_agent=None,
    ):
        if not isinstance(status_code, int):
            raise ValueError(f"status_code must be an integer, got {status_code!r}")

        UatPanRequestLog.objects.create(
            pan_number=pan_number,
            vendor=vendor_name,
            endpoint=endpoint,
            status_code=status_code,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload,
            error_message=error_message,
            user=user,
            pan_details=pan_details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
