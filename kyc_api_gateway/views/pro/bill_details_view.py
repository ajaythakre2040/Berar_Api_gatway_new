
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from kyc_api_gateway.models import (
    ProElectricityBill,
    ClientManagement,
    KycClientServicesManagement,
    KycVendorPriority
)
from kyc_api_gateway.serializers.pro_bill_details_serializer import ProElectricityBillSerializer
from kyc_api_gateway.services.pro.bill_handler import call_vendor_api, save_bill_data, normalize_vendor_response
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models.pro_bill_request_log import ProBillRequestLog


class ProBillDetailsAPIView(APIView):
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

        consumer_id = request.data.get("consumer_id")
        service_provider = request.data.get("service_provider")

        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # user = request.user if getattr(request.user, "is_authenticated", False) else None
        if not consumer_id or not service_provider or consumer_id.strip() == "":
            missing = []
            if not consumer_id or consumer_id.strip() == "":
                missing.append("consumer_id")
            if not service_provider or service_provider.strip() == "":
                missing.append("service_provider")
            
            error_msg = f"Missing required fields: {', '.join(missing)}"
            self._log_request(
                customer_id=consumer_id,
                service_provider=service_provider,
                vendor_name=None,
                endpoint=request.path,
                status_code=400,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 400,
                "error": error_msg
            }, status=400)


        client = self._authenticate_client(request)
        if isinstance(client, Response):
            return client

        service_name = "BILL"
        service_id = KYC_MY_SERVICES.get(service_name.upper())

        # print(f"[DEBUG] Authenticated service_id: {service_id}")
        if not service_id:

            self._log_request(
                customer_id=request.data.get("consumer_id") or request.data.get("id_number"),
                service_provider=service_provider,
                vendor_name=None,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=f"{service_name} service not configured",
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 500,
                "error": f"{service_name} service not configured"
            }, status=500)

        try:
            cache_days = self._get_cache_days(client, service_id)
        except PermissionError as e:
            self._log_request(
                customer_id=request.data.get("consumer_id") or request.data.get("id_number"),
                service_provider=service_provider,
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=None,
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
                customer_id=request.data.get("consumer_id") or request.data.get("id_number"),
                service_provider=service_provider,
                vendor_name=None,
                endpoint=request.path,
                status_code=500,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=str(e),
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )  
            return Response({
                "success": False,
                "status": 500,
                "error": str(e)
            }, status=500)


        days_ago = timezone.now() - timedelta(days=cache_days)
        customer_id = request.data.get("consumer_id") or request.data.get("id_number")

        cached = ProElectricityBill.objects.filter(
            customer_id=customer_id,
            created_at__gte=days_ago
        ).first()

        if cached:
            serializer = ProElectricityBillSerializer(cached)
            self._log_request(
                customer_id=customer_id,
                service_provider=service_provider,
                vendor_name="CACHE",
                endpoint=request.path,
                status_code=200,
                status="success",
                request_payload=request.data,
                response_payload=serializer.data,
                user=None,
                bill_details=cached,
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


        print(f"[DEBUG] Found {vendors.count()} priority vendors for client={client.id}, service_id={service_id}")
        print(f"[DEBUG] Vendors: {[vp.vendor.vendor_name for vp in vendors]}")



        if not vendors.exists():
            error_msg = f"No vendors assigned for this service"
            self._log_request(
                customer_id=consumer_id,
                service_provider=service_provider,  
                vendor_name=None,
                endpoint=request.path,
                status_code=403,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({
                "success": False,
                "status": 403,
                "error": "No vendors assigned for this service"
            }, status=403)

        endpoint = request.path

        for vp in vendors:
            vendor = vp.vendor
            try:
                response = call_vendor_api(vendor, request.data)

                if response and response.get("http_error"):

                    self._log_request(
                        customer_id=customer_id,
                        service_provider=service_provider,
                        vendor_name=vendor.vendor_name,
                        endpoint=endpoint,
                        status_code=502,
                        status="fail",
                        request_payload=request.data,
                        response_payload=response.get("vendor_response"),
                        error_message=response.get("error_message"),
                        user=None,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    continue

                try:
                    data = response.json()
                except Exception:
                    data = None

                normalized = normalize_vendor_response(vendor.vendor_name, data or {})
                if not normalized:
                    self._log_request(
                        customer_id=customer_id,
                        service_provider=service_provider,
                        vendor_name=vendor.vendor_name,
                        endpoint=endpoint,
                        status_code=204,
                        status="fail",
                        request_payload=request.data,
                        response_payload=getattr(response, 'text', None),
                        error_message="No valid data returned",
                        user=None,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    continue

                bill_obj = save_bill_data(normalized, client.id)
                serializer = ProElectricityBillSerializer(bill_obj)

                self._log_request(
                            customer_id=customer_id,
                            service_provider=service_provider,
                            vendor_name=vendor.vendor_name,
                            endpoint=endpoint,
                            status_code=200,
                            status="success",
                            request_payload=request.data,
                            response_payload=serializer.data,
                            error_message=None,
                            user=None,
                            bill_details=bill_obj,
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
                    customer_id=customer_id,
                    service_provider=service_provider,
                    vendor_name=vendor.vendor_name,
                    endpoint=endpoint,
                    status_code=500,
                    status="fail",
                    request_payload=request.data,
                    response_payload=None,
                    error_message=str(e),
                    user=None,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                continue

        return Response({
            "success": False,
            "status": 404,
            "error": "No vendor returned valid data"
        }, status=404)


    def _authenticate_client(self, request):
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        api_key = request.headers.get("X-API-KEY")
        if not api_key:

            error_msg = "Missing API key"
            self._log_request(
                customer_id=None,
                service_provider=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
                user=None,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return Response({"success": False, "status": 401, "error": "Missing API key"}, status=401)

        client = ClientManagement.objects.filter(
            production_key=api_key,
            deleted_at__isnull=True
        ).first()

        if not client:
            error_msg = "Invalid API key"
            self._log_request(
                customer_id=None,
                service_provider=None,
                vendor_name=None,
                endpoint=request.path,
                status_code=401,
                status="fail",
                request_payload=request.data,
                response_payload=None,
                error_message=error_msg,
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
            raise PermissionError(f"Service is not permitted for client")

        return cs.day

    def _get_priority_vendors(self, client, service_id):
        return KycVendorPriority.objects.filter(
            client=client,
            my_service_id=service_id,
            deleted_at__isnull=True
        ).select_related("vendor").order_by("priority")
    
    def _log_request(self, customer_id, service_provider, vendor_name, endpoint, status_code, status, request_payload=None, response_payload=None, error_message=None, user=None, bill_details=None,ip_address=None,user_agent=None):

        if not isinstance(status_code, int):
            raise ValueError(f"status_code must be an integer, got {status_code!r}")

        ProBillRequestLog.objects.create(
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
            user=None,
            ip_address=ip_address,
            user_agent=user_agent
        )
