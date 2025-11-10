from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone
from kyc_api_gateway.models import (
    UatDrivingLicense,
    ClientManagement,
    KycClientServicesManagement,
    KycVendorPriority,
)
from kyc_api_gateway.models.uat_driving_license_log import UatDrivingLicenseRequestLog
from kyc_api_gateway.serializers.uat_driving_serializer import UatDrivingLicenseSerializer
from kyc_api_gateway.services.uat.driving_license_handler import (
    call_vendor_api_uat,
    normalize_vendor_response,
    save_uat,
)
from constant import KYC_MY_SERVICES
import re

class UatDrivingLicenseAPIView(APIView):

    authentication_classes = []
    permission_classes = []

    @staticmethod
    def sanitize_input(value):
        if not value:
            return value
        value = value.strip()

        clean_value = re.sub(r"<.*?>", "", value)

        if re.search(r"(script|alert|onerror|onload|<|>|javascript:)", clean_value, re.IGNORECASE):
            raise ValueError("Invalid characters detected in input.")

        return clean_value


    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def post(self, request):

        try:
            license_no = self.sanitize_input(request.data.get("license_no"))
            dob = self.sanitize_input(request.data.get("dob"))
        except ValueError as e:
            return Response({
                "success": False,
                "status": 400,
                "error": str(e)
            }, status=400)
    

        if not license_no or not dob:
            missing = []
            if not license_no:
                missing.append("license_no")
            if not dob:
                missing.append("dob")
            error_msg = f"Missing required fields: {', '.join(missing)}"
            self._log_request(
                dl_number=license_no,
                name=None,
                vendor=None,
                endpoint=request.path,
                status_code=400,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                dl_obj=None,
                created_by=None,
            )
            return Response({"success": False, "status": 400, "error": error_msg}, status=400)

        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client

        service_name = "DRIVING"
        service_id = KYC_MY_SERVICES.get(service_name.upper())
        if not service_id:
            error_msg = f"{service_name} service not assigned to client"
            self._log_request(
                dl_number=license_no,
                name=None,
                vendor=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                dl_obj=None,
                created_by=client.id,
            )
            return Response({"success": False, "status": 403, "error": error_msg}, status=403)

        try:
            cache_days = self._get_cache_days(client, service_id)
        except (PermissionError, ValueError) as e:
            self._log_request(
                dl_number=license_no,
                name=None,
                vendor=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                dl_obj=None,
                created_by=client.id,
            )
            return Response({"success": False, "status": 403, "error": str(e)}, status=403)

        days_ago = timezone.now() - timedelta(days=cache_days)

        dob_date = None
        dob_str = dob.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                dob_date = datetime.strptime(dob_str, fmt).date()
                break
            except ValueError:
                continue

        if dob_date is None:
            return Response({"success": False, "status": 400, "error": "Invalid DOB format"}, status=400)


        license_no_clean = license_no.strip().upper()

        cached = UatDrivingLicense.objects.filter(
            dl_number__iexact=license_no_clean,
            dob=dob_date,
            created_at__gte=days_ago,
        ).first()

        if cached:
            serializer = UatDrivingLicenseSerializer(cached)
            self._log_request(
                dl_number=cached.dl_number,
                name=cached.name,
                vendor="cached",
                endpoint=request.path,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                error_message=None,
                dl_obj=cached,
                created_by=client.id,
            )
            return Response(
                {"success": True, "status": 200, "message": "Cached data", "data": serializer.data}
            )

        vendors = self._get_priority_vendors(client, service_id)
        if not vendors.exists():
            error_msg = "No vendors configured for Driving License service"
            self._log_request(
                dl_number=license_no,
                name=None,
                vendor=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                dl_obj=None,
                created_by=client.id,
            )
            return Response({"success": False, "status": 403, "error": error_msg}, status=403)

        for vp in vendors:
            vendor = vp.vendor
            try:
                response = call_vendor_api_uat(vendor, request.data)

                if response and isinstance(response, dict) and response.get("http_error"):
                    self._log_request(
                        dl_number=license_no,
                        name=None,
                        vendor=vendor.vendor_name,
                        endpoint=request.path,
                        status_code=response.get("status_code") or 500,
                        status="fail",
                        request_payload=request.data,
                        response_payload=response.get("vendor_response"),
                        error_message=response.get("error_message"),
                        dl_obj=None,
                        created_by=client.id,
                    )
                    continue

                try:
                    data = response

                except Exception:
                    data = None

                normalized = normalize_vendor_response(vendor.vendor_name, data or {}, request.data)
                if not normalized:

                    print("No vendor returned valid data")

                    self._log_request(
                        dl_number=license_no,
                        name=None,
                        vendor=vendor.vendor_name,
                        endpoint=request.path,
                        status_code=502,
                        status="fail",
                        request_payload=request.data,
                        response_payload=data,
                        error_message=f"Normalization failed for vendor {vendor.vendor_name}",
                        dl_obj=None,
                        created_by=client.id,
                    )
                    continue

                dl_obj = save_uat(normalized, client.id)
                serializer = UatDrivingLicenseSerializer(dl_obj)

                self._log_request(
                    dl_number=dl_obj.dl_number,
                    name=dl_obj.name,
                    vendor=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    error_message=None,
                    dl_obj=dl_obj,
                    created_by=client.id,
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
                    dl_number=license_no,
                    name=None,
                    vendor=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=500,
                    status="fail",
                    request_payload=request.data,
                    response_payload=None,
                    error_message=str(e),
                    dl_obj=None,
                    created_by=client.id,
                )
                continue

        return Response(
            {"success": False, "status": 404, "error": "No vendor returned valid data"}, status=404
        )


    def _authenticate_client(self, request):
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            self._log_request(
                dl_number=None,
                name=None,
                vendor=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Missing API key",
                dl_obj=None,
                created_by=None,

            )
            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(uat_key=api_key, deleted_at__isnull=True).first()
        if not client:
            self._log_request(
                dl_number=None,
                name=None,
                vendor=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Invalid API key",
                dl_obj=None,
                created_by=None,
            )
            return Response({"success": False, "status": 401, "error": "Invalid API key"}, status=401)

        return client

    def _get_cache_days(self, client, service_id):
        cs = KycClientServicesManagement.objects.filter(
            client=client, myservice__id=service_id, deleted_at__isnull=True
        ).first()
        if not cs:
            raise ValueError("Cache days not configured for this service")
        if cs.status is False:
            raise PermissionError("Service disabled for this client")
        return cs.day

    def _get_priority_vendors(self, client, service_id):
        return KycVendorPriority.objects.filter(
            client=client, my_service_id=service_id, deleted_at__isnull=True
        ).select_related("vendor").order_by("priority")

    def _log_request(
        self,
        dl_number=None,
        vendor=None,
        endpoint=None,
        status_code=500,
        status="fail",
        request_payload=None,
        response_payload=None,
        error_message=None,
        dl_obj=None,
        user=None,
        name=None,
        created_by=None,
    ):
        if not isinstance(status_code, int):
            status_code = 500

        UatDrivingLicenseRequestLog.objects.create(
            driving_license=dl_obj,
            dl_number=dl_number,
            vendor=vendor,
            endpoint=endpoint,
            status_code=status_code,
            status=status,
            request_payload=request_payload,
            response_payload=response_payload,
            error_message=error_message,
            user=user,
            name=name,
            created_by=created_by,
        )

