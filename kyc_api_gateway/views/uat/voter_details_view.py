from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from kyc_api_gateway.models import (
    UatVoterDetail,
    ClientManagement,
    KycClientServicesManagement,
    KycVendorPriority
)
from kyc_api_gateway.serializers.uat_voter_details_serializer import UatVoterDetailSerializer
from kyc_api_gateway.services.uat.voter_handler import (
    call_voter_vendor_api,
    normalize_vendor_response,
    save_voter_data
)
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.uat_voter_request_log import UatVoterRequestLog
from kyc_api_gateway.utils.sanitizer import sanitize_input


class UatVoterDetailsAPIView(APIView):
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

        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client
     
        try:
            voter_id = sanitize_input(request.data.get("id_number"))
            if voter_id:
                voter_id = voter_id.strip().upper()
        except ValueError as e:
            return Response({
                "success": False,
                "status": 400,
                "error": str(e)
            }, status=400)
    
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user if getattr(request.user, "is_authenticated", False) else None

        if not voter_id or voter_id.strip() == "":
            
            return Response({
                "success": False,
                "status": 400,
                "error": "Voter ID required"
            }, status=400)


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
                user_agent=user_agent,
                created_by=client.id
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
                user_agent=user_agent,
                created_by=client.id
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
                user_agent=user_agent,
                created_by=client.id
            )
            return Response({
                "success": False,
                "status": 500,
                "error": str(e)
            }, status=500)

        days_ago = timezone.now() - timedelta(days=cache_days)
        cached = UatVoterDetail.objects.filter(
            voter_id=voter_id,
            created_at__gte=days_ago
        ).first()

        if cached:
            serializer = UatVoterDetailSerializer(cached)
            self._log_request(
                voter_id=voter_id,
                vendor_name="cached",
                endpoint=request.path,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                user=user,
                voter_obj=cached,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id
            )

            message = (
                "Data from cache" if client.id == 1
                else "Data fetched successfully"
            )

            return Response({
                "success": True,
                "status": 200,
                "message": message,
                "data": serializer.data
            })

        vendors = self._get_priority_vendors(client, service_id)
        if not vendors.exists():
            error_msg = "No vendors assigned for this service"

            self._log_request(
                voter_id=voter_id,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=client.id
            )

            error_msg = (
                error_msg if client.id == 1
                else "Service currently not accessible"

            )

            return Response({
                "success": False,
                "status": 403,
                "error": error_msg
            }, status=403)

        for vp in vendors:
            vendor = vp.vendor

            try:
                response = call_voter_vendor_api(vendor, request.data)

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
                        user_agent=user_agent,
                        created_by=client.id
                    )
                    continue  
                try:
                    data = response

                except Exception:
                    data = None

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
                        user_agent=user_agent,
                        created_by=client.id
                    )
                    continue

                voter_obj = save_voter_data(normalized, client.id)
                serializer = UatVoterDetailSerializer(voter_obj)
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
                    user_agent=user_agent,
                    created_by=client.id
                )


                message = (
                    f"Data from {vendor.vendor_name}"
                    if client.id == 1
                    else "Data fetched successfully"
                )

                return Response({
                    "success": True,
                    "status": 200,
                    "message": message,
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
                    user_agent=user_agent,
                    created_by=client.id
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
            user_agent=user_agent,
            created_by=client.id
        )

        
        final_error_message = (
            "No vendor returned valid data. All vendor requests failed."
            if client.id == 1
            else "Unable to process the request at the moment. Please try again later."
        )
        
        return Response({
            "success": False,
            "status": 404,
            "error": final_error_message
        }, status=404)

    def _authenticate_client(self, request):
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        api_key = request.headers.get("X-API-KEY")

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
                user_agent=user_agent,
                created_by=client.id if client else None,
            )
            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(
            uat_key=api_key,
            deleted_at__isnull=True
        ).first()

        
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
                user_agent=user_agent,
                created_by=client.id if client else None,
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
        
        success_count = UatVoterRequestLog.objects.filter(
            created_by=client.id,
            status_code__in=["200", 200],
            status__iexact="success" 
        ).count()
        
        if success_count >= cs.uat_api_limit:
           
            raise PermissionError(f"UAT API limit exceeded")
        
        return cs.day

    def _get_priority_vendors(self, client, service_id):
        return KycVendorPriority.objects.filter(
            client=client,
            my_service_id=service_id,
            deleted_at__isnull=True
        ).select_related("vendor").order_by("priority")

    def _log_request(self, voter_id, vendor_name, endpoint, status_code, status,
                     request_payload=None, response_payload=None, error_message=None,
                     user=None, voter_obj=None, ip_address=None, user_agent=None, created_by=None):
        
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
            created_by=created_by
        )
