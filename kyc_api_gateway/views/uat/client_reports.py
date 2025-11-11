from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
import pandas as pd

from client_auth.permissions.authentication import ClientJWTAuthentication
from client_auth.permissions.permissions import IsClientAuthenticated
from kyc_api_gateway.utils.reports import get_filtered_queryset
from kyc_api_gateway.models import ClientManagement

from kyc_api_gateway.serializers.uat_pan_request_log_serializer import UatPanRequestLogSerializer
from kyc_api_gateway.serializers.uat_bill_request_log_serializer import UatBillRequestLogSerializer
from kyc_api_gateway.serializers.uat_voter_details_log_serializer import UatVoterRequestLogSerializer
from kyc_api_gateway.serializers.uat_name_request_match_log_serializer import UatNameMatchRequestLogSerializer
from kyc_api_gateway.serializers.uat_rc_detail_log_serializer import UatRcRequestLogSerializer
from kyc_api_gateway.serializers.uat_driving_license_log_serializer import UatDrivingLicenseRequestLogSerializer
from kyc_api_gateway.serializers.uat_passport_log_serializer import UatPassportRequestLogSerializer
from kyc_api_gateway.serializers.uat_address_log_serializer import UatAddressMatchRequestLogSerializer

from rest_framework.permissions import IsAuthenticated
from auth_system.permissions.token_valid import IsTokenValid


SERIALIZER_MAP = {
    "PAN": UatPanRequestLogSerializer,
    "BILL": UatBillRequestLogSerializer,
    "VOTER": UatVoterRequestLogSerializer,
    "NAME": UatNameMatchRequestLogSerializer,
    "RC": UatRcRequestLogSerializer,
    "DRIVING": UatDrivingLicenseRequestLogSerializer,
    "PASSPORT": UatPassportRequestLogSerializer,
    "ADDRESS": UatAddressMatchRequestLogSerializer,
}

from client_auth.models.login_session import LoginSession

class ClientReportAPIView(APIView):
    """
    ✅ Clients can only view their own report.
    Even if they send another client_id, it will be ignored.
    """
    permission_classes = [IsAuthenticated, IsTokenValid]

    def post(self, request):
        client_id = getattr(request.user, "id", None)
        if not client_id:
            return Response({"success": False, "message": "Unauthorized client"}, status=401)

        client_id = client.id

        print("Client ID from authenticated user:", client_id)


        active_session = LoginSession.objects.filter(
            client_id=client_id,
            is_active=True
        ).order_by("-login_at").first()

        print("Client ID from token:", client_id)


        request.data["client_id"] = client_id
        queryset, service_name, error = get_filtered_queryset(request.data)


        print("Filtered queryset obtained:", queryset)
        
        if error:
            return Response({"success": False, "message": error}, status=400)

        queryset = queryset.filter(created_by=client_id)

        print(f"Queryset for service {service_name} and client {client_id} has {queryset.count()} records.")

        
        if not queryset.exists():
            return Response({"success": False, "message": "No records found."}, status=404)

        serializer_class = SERIALIZER_MAP.get(service_name)


        print("Using serializer class:", serializer_class)

        if not serializer_class:
            return Response({"success": False, "message": f"No serializer for {service_name}"}, status=400)

        serializer = serializer_class(queryset, many=True)
        return Response({
            "success": True,
            "service": service_name,
            "client_name": getattr(client, "company_name", "Unknown"),
            "count": queryset.count(),
            "data": serializer.data
        }, status=200)





class ClientReportDownloadAPIView(APIView):
 
    authentication_classes = [ClientJWTAuthentication]
    permission_classes = [IsClientAuthenticated]
    def post(self, request):
        client = request.user
        if not client or not getattr(client, "id", None):
            return Response({"success": False, "message": "Unauthorized client"}, status=401)

        client_id = client.id

        active_session = LoginSession.objects.filter(
            client_id=client_id,
            is_active=True
        ).order_by("-login_at").first()

        if not active_session:
            return Response({
                "success": False,
                "message": "Session expired or not logged in. Please login again."
            }, status=401)

        if active_session.expiry_at and active_session.expiry_at < timezone.now():
            active_session.is_active = False
            active_session.save(update_fields=["is_active"])
            return Response({
                "success": False,
                "message": "Session expired. Please login again."
            }, status=401)

        request.data["client_id"] = client_id
        queryset, service_name, error = get_filtered_queryset(request.data)
        if error:
            return Response({"success": False, "message": error}, status=400)

        queryset = queryset.filter(created_by=client_id)
        if not queryset.exists():
            return Response({"success": False, "message": "No records found."}, status=404)

        df = pd.DataFrame(list(queryset.values()))
        df.insert(0, "service_name", service_name)

        client = ClientManagement.objects.filter(id=client_id).first()
        client_name = client.name if client else "Unknown"
        df["client_name"] = client_name

        drop_columns = [
            "id", "deleted_at", "updated_at", "created_by", "created_at", "request_id",
            "pan_details_id", "bill_details_id", "voter_detail_id", "name_match_id",
            "rc_details_id", "driving_license_id", "passport_verification_id",
            "address_match_id", "user_id"
        ]
        df.drop(columns=[c for c in drop_columns if c in df.columns], inplace=True, errors="ignore")

        response = HttpResponse(content_type="text/csv")
        filename = f"{service_name}_ClientReport_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        df.to_csv(response, index=False)
        return response
