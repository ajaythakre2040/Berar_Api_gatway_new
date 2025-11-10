# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.utils.dateparse import parse_date
# from django.http import HttpResponse
# import pandas as pd

# from auth_system.permissions.token_valid import IsTokenValid
# from auth_system.utils.pagination import CustomPagination

# from rest_framework import status
# from constant import KYC_MY_SERVICES


# from kyc_api_gateway.models import (
#     KycMyServices,
#     VendorManagement,
#     ClientManagement,
#     KycVendorPriority,
#     UatNameMatchRequestLog,
#     UatPanRequestLog,
#     UatRcRequestLog,
#     UatAddressMatchRequestLog,
#     UatDrivingLicenseRequestLog,
#     UatPassportRequestLog,
#     UatBillRequestLog,
# )

# from kyc_api_gateway.models import (
#     UatPanRequestLog,
#     UatBillRequestLog,
#     UatDrivingLicenseRequestLog,
#     UatNameMatchRequestLog,
#     UatPassportRequestLog,
#     UatRcRequestLog,
#     UatVoterRequestLog,
#     UatAddressMatchRequestLog
# )

# from kyc_api_gateway.serializers.uat_pan_request_log_serializer import UatPanRequestLogSerializer
# from kyc_api_gateway.serializers.uat_address_log_serializer import UatAddressMatchRequestLogSerializer
# from kyc_api_gateway.serializers.uat_bill_request_log_serializer import UatBillRequestLogSerializer
# from kyc_api_gateway.serializers.uat_driving_license_log_serializer import UatDrivingLicenseRequestLogSerializer
# from kyc_api_gateway.serializers.uat_name_request_match_log_serializer import UatNameMatchRequestLogSerializer

# from kyc_api_gateway.serializers.uat_passport_log_serializer import UatPassportRequestLogSerializer
# from kyc_api_gateway.serializers.uat_rc_detail_log_serializer import UatRcRequestLogSerializer
# from kyc_api_gateway.serializers.uat_voter_details_log_serializer import UatVoterRequestLogSerializer

# SERVICE_LOG_MAPPING = {
#     "PAN": UatPanRequestLog,
#     "BILL": UatBillRequestLog,
#     "VOTER": UatDrivingLicenseRequestLog,
#     "NAME": UatNameMatchRequestLog,
#     "RC": UatRcRequestLog,
#     "DRIVING": UatDrivingLicenseRequestLog,
#     "PASSPORT": UatPassportRequestLog,
#     "ADDRESS": UatAddressMatchRequestLog,
# }


# class ReportAPIView(APIView):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):
#         try:
#             myservice_id = request.data.get("myservice_id")
#             vendor_name = request.data.get("vendor_name")
#             status_code = request.data.get("status_code")
#             from_date = request.data.get("from_date")
#             to_date = request.data.get("to_date")
#             client_id = request.data.get("client_id")

#             if not myservice_id:
#                 return Response({
#                     "success": False,
#                     "message": "myservice_id is required"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # ✅ Base queryset selection
#             if myservice_id == KYC_MY_SERVICES.get("PAN"):
#                 queryset = UatPanRequestLog.objects.all()
#                 serializer_class = UatPanRequestLogSerializer
#                 service_name = "PAN"

#             elif myservice_id == KYC_MY_SERVICES.get("BILL"):
#                 queryset = UatBillRequestLog.objects.all()
#                 serializer_class = UatBillRequestLogSerializer
#                 service_name = "BILL"

#             elif myservice_id == KYC_MY_SERVICES.get("VOTER"):
#                 queryset = UatVoterRequestLog.objects.all()
#                 serializer_class = UatVoterRequestLogSerializer
#                 service_name = "VOTER"

#             elif myservice_id == KYC_MY_SERVICES.get("NAME"):
#                 queryset = UatNameMatchRequestLog.objects.all()
#                 serializer_class = UatNameMatchRequestLogSerializer
#                 service_name = "NAME"

#             elif myservice_id == KYC_MY_SERVICES.get("RC"):
#                 queryset = UatRcRequestLog.objects.all()
#                 serializer_class = UatRcRequestLogSerializer
#                 service_name = "RC"

#             elif myservice_id == KYC_MY_SERVICES.get("DRIVING"):
#                 queryset = UatDrivingLicenseRequestLog.objects.all()
#                 serializer_class = UatDrivingLicenseRequestLogSerializer
#                 service_name = "DRIVING"

#             elif myservice_id == KYC_MY_SERVICES.get("PASSPORT"):
#                 queryset = UatPassportRequestLog.objects.all()
#                 serializer_class = UatPassportRequestLogSerializer
#                 service_name = "PASSPORT"

#             elif myservice_id == KYC_MY_SERVICES.get("ADDRESS"):
#                 queryset = UatAddressMatchRequestLog.objects.all()
#                 serializer_class = UatAddressMatchRequestLogSerializer
#                 service_name = "ADDRESS"

#             else:
#                 return Response({
#                     "success": False,
#                     "message": "Unsupported myservice_id"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             if vendor_name:
#                 queryset = queryset.filter(vendor__iexact=vendor_name.strip())

#             if status_code:
#                 queryset = queryset.filter(status_code=status_code)

#             if client_id:
#                 queryset = queryset.filter(created_by=client_id)


#             if from_date or to_date:
#                 from_date_parsed = parse_date(from_date) if from_date else None
#                 to_date_parsed = parse_date(to_date) if to_date else None

#                 if from_date_parsed and to_date_parsed:
#                     if from_date_parsed > to_date_parsed:
#                         from_date_parsed, to_date_parsed = to_date_parsed, from_date_parsed
#                     queryset = queryset.filter(created_at__date__range=[from_date_parsed, to_date_parsed])
#                 elif from_date_parsed:
#                     queryset = queryset.filter(created_at__date__gte=from_date_parsed)
#                 elif to_date_parsed:
#                     queryset = queryset.filter(created_at__date__lte=to_date_parsed)

#             queryset = queryset.order_by("-created_at")
#             serializer = serializer_class(queryset, many=True)

#             data = serializer.data
#             # ✅ Add client_name based on client_id
#             for item in data:
#                 client_id = item.get("created_by")
#                 if client_id:
#                     client_obj = ClientManagement.objects.filter(id=client_id).first()
#                     item["client_name"] = client_obj.name if client_obj else None
#                 else:
#                     item["client_name"] = None

#             return Response({
#                 "success": True,
#                 "service": service_name,
#                 "count": queryset.count(),
#                 "data": data
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "success": False,
#                 "error": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

# class KycReportDownloadAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsTokenValid]

#     def post(self, request):
#         try:
#             myservice_id = request.data.get("myservice_id")
#             vendor_name = request.data.get("vendor_name")
#             status_code = request.data.get("status_code")
#             from_date = request.data.get("from_date")
#             to_date = request.data.get("to_date")
#             client_id = request.data.get("client_id")

#             if not myservice_id:
#                 return Response({
#                     "success": False,
#                     "message": "myservice_id is required"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # ✅ Map service id → model
#             service_map = {
#                 KYC_MY_SERVICES.get("PAN"): (UatPanRequestLog, "PAN_Report.csv"),
#                 KYC_MY_SERVICES.get("BILL"): (UatBillRequestLog, "BILL_Report.csv"),
#                 KYC_MY_SERVICES.get("VOTER"): (UatVoterRequestLog, "VOTER_Report.csv"),
#                 KYC_MY_SERVICES.get("NAME"): (UatNameMatchRequestLog, "NAME_Report.csv"),
#                 KYC_MY_SERVICES.get("RC"): (UatRcRequestLog, "RC_Report.csv"),
#                 KYC_MY_SERVICES.get("DRIVING"): (UatDrivingLicenseRequestLog, "DRIVING_Report.csv"),
#                 KYC_MY_SERVICES.get("PASSPORT"): (UatPassportRequestLog, "PASSPORT_Report.csv"),
#                 KYC_MY_SERVICES.get("ADDRESS"): (UatAddressMatchRequestLog, "ADDRESS_Report.csv"),
#             }

#             model_info = service_map.get(myservice_id)
#             if not model_info:
#                 return Response({
#                     "success": False,
#                     "message": "Unsupported myservice_id"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             model, filename = model_info
#             queryset = model.objects.all().order_by("-created_at")

#             # ✅ Apply filters
#             if vendor_name:
#                 # Case-insensitive + trim-safe
#                 queryset = queryset.filter(vendor__iexact=vendor_name.strip())

#             if status_code:
#                 queryset = queryset.filter(status_code=status_code)

#             if client_id:
#                 queryset = queryset.filter(created_by=client_id)

#             # ✅ Date filters
#             if from_date or to_date:
#                 from_date_parsed = parse_date(from_date) if from_date else None
#                 to_date_parsed = parse_date(to_date) if to_date else None

#                 if from_date_parsed and to_date_parsed:
#                     if from_date_parsed > to_date_parsed:
#                         from_date_parsed, to_date_parsed = to_date_parsed, from_date_parsed
#                     queryset = queryset.filter(created_at__date__range=[from_date_parsed, to_date_parsed])
#                 elif from_date_parsed:
#                     queryset = queryset.filter(created_at__date__gte=from_date_parsed)
#                 elif to_date_parsed:
#                     queryset = queryset.filter(created_at__date__lte=to_date_parsed)

#             if not queryset.exists():
#                 return Response({
#                     "success": False,
#                     "message": "No records found for this service."
#                 }, status=status.HTTP_404_NOT_FOUND)

          
#             df = pd.DataFrame(list(queryset.values()))

#             if "created_by" in df.columns:
#                 client_map = {
#                     c.id: c.name for c in ClientManagement.objects.filter(
#                         id__in=df["created_by"].dropna().unique()
#                     )
#                 }
#                 df["client_name"] = df["created_by"].map(client_map)

#             # ✅ Add service_name column (determine type by service ID)
#             service_name_map = {
#                 KYC_MY_SERVICES.get("PAN"): "PAN",
#                 KYC_MY_SERVICES.get("BILL"): "BILL",
#                 KYC_MY_SERVICES.get("VOTER"): "VOTER",
#                 KYC_MY_SERVICES.get("NAME"): "NAME MATCH",
#                 KYC_MY_SERVICES.get("RC"): "RC",
#                 KYC_MY_SERVICES.get("DRIVING"): "DRIVING",
#                 KYC_MY_SERVICES.get("PASSPORT"): "PASSPORT",
#                 KYC_MY_SERVICES.get("ADDRESS"): "ADDRESS",
#             }
#             df["service_name"] = service_name_map.get(myservice_id, "UNKNOWN")

#             # ✅ Reorder columns → move service_name to the front
#             cols = ["service_name"] + [col for col in df.columns if col != "service_name"]
#             df = df[cols]

#             # ✅ Drop unnecessary columns
#             drop_columns = ["id", "deleted_at", "updated_at", "created_by", "created_at", "pan_details_id", "user_id"]
#             df.drop(columns=[c for c in drop_columns if c in df.columns], inplace=True, errors="ignore")

#             # ✅ Create CSV response
#             response = HttpResponse(content_type="xlsx/csv")
#             response["Content-Disposition"] = f'attachment; filename="{filename}"'
#             df.to_csv(path_or_buf=response, index=False)
#             return response

#         except Exception as e:
#             return Response({
#                 "success": False,
#                 "error": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# kyc_api_gateway/views/report_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
import pandas as pd

from kyc_api_gateway.utils.reports import get_filtered_queryset
from kyc_api_gateway.models import ClientManagement

# ✅ Import all serializers (if you want dynamic handling)
from kyc_api_gateway.serializers.uat_pan_request_log_serializer import UatPanRequestLogSerializer
from kyc_api_gateway.serializers.uat_bill_request_log_serializer import UatBillRequestLogSerializer
from kyc_api_gateway.serializers.uat_voter_details_log_serializer import UatVoterRequestLogSerializer
from kyc_api_gateway.serializers.uat_name_request_match_log_serializer import UatNameMatchRequestLogSerializer
from kyc_api_gateway.serializers.uat_rc_detail_log_serializer import UatRcRequestLogSerializer
from kyc_api_gateway.serializers.uat_driving_license_log_serializer import UatDrivingLicenseRequestLogSerializer
from kyc_api_gateway.serializers.uat_passport_log_serializer import UatPassportRequestLogSerializer
from kyc_api_gateway.serializers.uat_address_log_serializer import UatAddressMatchRequestLogSerializer


# ✅ Mapping for dynamic serializer use
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


class ReportAPIView(APIView):
    def post(self, request):
        queryset, service_name, error = get_filtered_queryset(request.data)
        if error:
            return Response({"success": False, "message": error}, status=status.HTTP_400_BAD_REQUEST)

        if not queryset.exists():
            return Response({"success": False, "message": "No records found."}, status=status.HTTP_404_NOT_FOUND)

        serializer_class = SERIALIZER_MAP.get(service_name)
        serializer = serializer_class(queryset, many=True) if serializer_class else None

        return Response({
            "success": True,
            "service": service_name,
            "count": queryset.count(),
            "data": serializer.data if serializer else []
        }, status=status.HTTP_200_OK)



class KycReportDownloadAPIView(APIView):
    def post(self, request):
        queryset, service_name, error = get_filtered_queryset(request.data)
        if error:
            return Response({"success": False, "message": error}, status=status.HTTP_400_BAD_REQUEST)

        if not queryset.exists():
            return Response({"success": False, "message": "No records found."}, status=status.HTTP_404_NOT_FOUND)

        df = pd.DataFrame(list(queryset.values()))

        # ✅ Add service name as the first column
        df.insert(0, "service_name", service_name)

        # ✅ Add client_name mapping
        if "created_by" in df.columns:
            client_map = {
                c.id: c.name for c in ClientManagement.objects.filter(
                    id__in=df["created_by"].dropna().unique()
                )
            }
            df["client_name"] = df["created_by"].map(client_map)

        # ✅ Drop unwanted columns if needed
        drop_columns = ["id", "deleted_at", "updated_at", "created_by", "created_at", "pan_details_id", "user_id","bill_details_id","voter_detail_id","name_match_id","rc_details_id","driving_license_id","passport_verification_id","address_match_id","request_id"]

        # drop_columns = ["id", "updated_at", "deleted_at"]
        df.drop(columns=[c for c in drop_columns if c in df.columns], inplace=True, errors="ignore")

        # ✅ Generate downloadable CSV
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{service_name}_Report.csv"'
        df.to_csv(response, index=False)
        return response
