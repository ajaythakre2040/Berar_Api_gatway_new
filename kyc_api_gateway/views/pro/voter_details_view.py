from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from kyc_api_gateway.models import (
    ProVoterDetail,
    ClientManagement,
    KycClientServicesManagement,
    KycVendorPriority
)
from kyc_api_gateway.serializers.pro_voter_details_serializer import ProVoterDetailSerializer
from kyc_api_gateway.services.pro.voter_handler import (
    call_voter_vendor_api,
    normalize_vendor_response,
    save_voter_data
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.pro_voter_request_log import ProVoterRequestLog


class ProVoterDetailsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def post(self, request):
        voter_id = (request.data.get("id_number") or "").strip().upper()
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user if getattr(request.user, "is_authenticated", False) else None

        if not voter_id or voter_id.strip() == "":
            self._log_request(
                voter_id=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=400,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Missing required field: id_number",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 400,
                "error": "Voter ID required"
            }, status=400)

        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client

        service_name = "VOTER"
        service_id = KYC_MY_SERVICES.get(service_name.upper())
        if not service_id:
            self._log_request(
                voter_id=voter_id,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=f"{service_name} service not configured",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 403,
                "error": f"{service_name} service not configured"
            }, status=403)

        try:
            cache_days = self._get_cache_days(client, service_id)
        except PermissionError as e:
            self._log_request(
                voter_id=voter_id,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 403,
                "error": str(e)
            }, status=403)
        except ValueError as e:
            self._log_request(
                voter_id=voter_id,
                vendor_name=None,
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
            return Response({
                "success": False,
                "status": 500,
                "error": str(e)
            }, status=500)

        days_ago = timezone.now() - timedelta(days=cache_days)
        cached = ProVoterDetail.objects.filter(
            voter_id=voter_id,
            created_at__gte=days_ago
        ).first()

        if cached:
            serializer = ProVoterDetailSerializer(cached)
            self._log_request(
                voter_id=voter_id,
                vendor_name="CACHE",
                endpoint=request.path,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                user=user,
                voter_obj=cached,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": True,
                "status": 200,
                "message": "Cached data",
                "data": serializer.data
            })

        vendors = self._get_priority_vendors(client, service_id)
        if not vendors.exists():
            self._log_request(
                voter_id=voter_id,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="No vendors assigned for this service",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 403,
                "error": "No vendors assigned for this service"
            }, status=403)

        for vp in vendors:
            vendor = vp.vendor
            try:
                response = call_voter_vendor_api(vendor, request.data)

                print('response', response)
                
                if response and response.get("http_error"):
                    self._log_request(
                        voter_id=voter_id,
                        vendor_name=vendor.vendor_name,
                        endpoint=request.path,
                        status_code=response.get("status_code") or 500,
                        status="fail",
                        request_payload=request.data,
                        response_payload=response.get("vendor_response"),
                        error_message=response.get("error_message"),
                        user=user,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    continue  # try next vendor
                try:
                    data = response

                    # print('this is data print try', data)
                except Exception:
                    data = None
                    # print('this is data print Exception', data)

                normalized = normalize_vendor_response(vendor.vendor_name, data or {})

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
                    continue

                voter_obj = save_voter_data(normalized, client.id)
                serializer = ProVoterDetailSerializer(voter_obj)
                self._log_request(
                    voter_id=voter_id,
                    vendor_name=vendor.vendor_name,
                    endpoint=request.path,
                    status_code=200,
                    status="success",
                    request_payload=request.data,
                    response_payload=serializer.data,
                    user=user,
                    voter_obj=voter_obj,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return Response({
                    "success": True,
                    "status": 200,
                    "message": f"Data from {vendor.vendor_name}",
                    "data": serializer.data
                })

            except Exception as e:
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
                continue

        self._log_request(
            voter_id=voter_id,
            vendor_name=None,
            endpoint=request.path,
            status_code=404,
            status="fail",
            request_payload=request.data,
            response_payload=None,
            error_message="No vendor returned valid data",
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return Response({
            "success": False,
            "status": 404,
            "error": "No vendor returned valid data"
        }, status=404)

    def _authenticate_client(self, request):
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        api_key = request.headers.get("X-API-KEY")

        print('_authenticate_client', api_key)
        if not api_key:
            self._log_request(
                voter_id=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Missing API key",
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(
            production_key=api_key,
            deleted_at__isnull=True
        ).first()


        print('_authenticate_client client', client)
        
        if not client:
            self._log_request(
                voter_id=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message="Invalid API key",
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({"success": False, "status": 401, "error": "Invalid API key"}, status=401)

        return client

    def _get_cache_days(self, client, service_id):
        cs = KycClientServicesManagement.objects.filter(
            client=client,
            myservice__id=service_id,
            deleted_at__isnull=True
        ).first()
        if not cs:
            raise ValueError(f"Cache days not configured for client={client.id}, service_id={service_id}")
        if cs.status is False:
            raise PermissionError("Service is not permitted for client")
        return cs.day

    def _get_priority_vendors(self, client, service_id):
        return KycVendorPriority.objects.filter(
            client=client,
            my_service_id=service_id,
            deleted_at__isnull=True
        ).select_related("vendor").order_by("priority")

    def _log_request(self, voter_id, vendor_name, endpoint, status_code, status,
                     request_payload=None, response_payload=None, error_message=None,
                     user=None, voter_obj=None, ip_address=None, user_agent=None):
        ProVoterRequestLog.objects.create(
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
            user_agent=user_agent
        )
