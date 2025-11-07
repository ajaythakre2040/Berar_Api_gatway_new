# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.db.models import Q
# from django.utils.dateparse import parse_date
# from django.http import HttpResponse
# import pandas as pd
# from datetime import date

# from auth_system.permissions.token_valid import IsTokenValid
# from auth_system.utils.pagination import CustomPagination

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


# class KycReportAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsTokenValid]

#     def post(self, request):
#         data = request.data
#         filters = Q()

#         client_id = data.get("client_id")
#         vendor_id = data.get("vendor_id")
#         myservice_id = data.get("myservice_id")
#         status_val = data.get("status")
#         from_date = data.get("from_date")
#         to_date = data.get("to_date")
#         today_only = data.get("today", False)

#         # Service validation
#         my_service = KycMyServices.objects.filter(id=myservice_id).first()
#         if not my_service:
#             return Response({"success": False, "message": "Invalid service"}, status=400)

#         log_model = SERVICE_LOG_MAPPING.get(my_service.name.upper())
#         if not log_model:
#             return Response({"success": False, "message": f"No log table mapped for {my_service.name}"}, status=400)

#         # ---- Filters ----
#         if today_only:
#             filters &= Q(created_at__date=date.today())

#         if from_date:
#             from_date = parse_date(from_date)
#             if not from_date:
#                 return Response({"success": False, "message": "Invalid 'from_date' format"}, status=400)
#             if to_date:
#                 to_date = parse_date(to_date)
#                 if not to_date:
#                     return Response({"success": False, "message": "Invalid 'to_date' format"}, status=400)
#                 filters &= Q(created_at__date__range=[from_date, to_date])
#             else:
#                 filters &= Q(created_at__date=from_date)
#         elif to_date:
#             to_date = parse_date(to_date)
#             if not to_date:
#                 return Response({"success": False, "message": "Invalid 'to_date' format"}, status=400)
#             filters &= Q(created_at__date=to_date)

#         if client_id:
#             filters &= Q(client_id=client_id)
#         if vendor_id:
#             filters &= Q(vendor_id=vendor_id)
#         if status_val:
#             filters &= Q(status__iexact=status_val)

#         logs = log_model.objects.filter(filters).select_related("client", "vendor").order_by("-id")

#         # Pagination
#         paginator = CustomPagination()
#         page_data = paginator.paginate_queryset(logs, request)

#         serialized_data = []
#         for log in page_data:
#             # Fetch priority if exists
#             priority = KycVendorPriority.objects.filter(
#                 client=log.client, vendor=log.vendor, my_service=my_service
#             ).first()
#             serialized_data.append({
#                 "Client Name": log.client.company_name if log.client else "",
#                 "Client Contact": log.client.phone if log.client else "",
#                 "Client Email": log.client.email if log.client else "",
#                 "Business Type": log.client.business_type if log.client else "",
#                 "Registration Number": log.client.registration_number if log.client else "",
#                 "Industry": log.client.industry if log.client else "",
#                 "Vendor Name": log.vendor.vendor_name if log.vendor else "",
#                 "Service": my_service.name,
#                 "Status": getattr(log, "status", ""),
#                 "Request ID": getattr(log, "request_id", ""),
#                 "Created At": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
#                 "Priority": priority.priority if priority else "",
#             })

#         return paginator.get_custom_paginated_response(
#             data=serialized_data,
#             extra_fields={"success": True, "message": "KYC Report fetched successfully"},
#         )


# class KycReportDownloadAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsTokenValid]

#     def post(self, request):
#         data = request.data
#         filters = Q()

#         client_id = data.get("client_id")
#         vendor_id = data.get("vendor_id")
#         myservice_id = data.get("myservice_id")
#         status_val = data.get("status")
#         from_date = data.get("from_date")
#         to_date = data.get("to_date")
#         today_only = data.get("today", False)

#         my_service = KycMyServices.objects.filter(id=myservice_id).first()
#         if not my_service:
#             return Response({"success": False, "message": "Invalid service"}, status=400)

#         log_model = SERVICE_LOG_MAPPING.get(my_service.name.upper())
#         if not log_model:
#             return Response({"success": False, "message": f"No log table mapped for {my_service.name}"}, status=400)

#         if today_only:
#             filters &= Q(created_at__date=date.today())

#         if from_date:
#             from_date = parse_date(from_date)
#             if not from_date:
#                 return Response({"success": False, "message": "Invalid 'from_date' format"}, status=400)
#             if to_date:
#                 to_date = parse_date(to_date)
#                 if not to_date:
#                     return Response({"success": False, "message": "Invalid 'to_date' format"}, status=400)
#                 filters &= Q(created_at__date__range=[from_date, to_date])
#             else:
#                 filters &= Q(created_at__date=from_date)
#         elif to_date:
#             to_date = parse_date(to_date)
#             if not to_date:
#                 return Response({"success": False, "message": "Invalid 'to_date' format"}, status=400)
#             filters &= Q(created_at__date=to_date)

#         if client_id:
#             filters &= Q(client_id=client_id)
#         if vendor_id:
#             filters &= Q(vendor_id=vendor_id)
#         if status_val:
#             filters &= Q(status__iexact=status_val)

#         logs = log_model.objects.filter(filters).select_related("client", "vendor").order_by("-id")

#         rows = []
#         for log in logs:
#             priority = KycVendorPriority.objects.filter(
#                 client=log.client, vendor=log.vendor, my_service=my_service
#             ).first()
#             rows.append({
#                 "Client Name": log.client.company_name if log.client else "",
#                 "Client Contact": log.client.phone if log.client else "",
#                 "Client Email": log.client.email if log.client else "",
#                 "Business Type": log.client.business_type if log.client else "",
#                 "Registration Number": log.client.registration_number if log.client else "",
#                 "Industry": log.client.industry if log.client else "",
#                 "Vendor Name": log.vendor.vendor_name if log.vendor else "",
#                 "Service": my_service.name,
#                 "Status": getattr(log, "status", ""),
#                 "Request ID": getattr(log, "request_id", ""),
#                 "Created At": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
#                 "Priority": priority.priority if priority else "",
#             })

#         df = pd.DataFrame(rows)
#         response = HttpResponse(content_type='application/vnd.ms-excel')
#         response['Content-Disposition'] = f'attachment; filename="{my_service.name}_kyc_report.xlsx"'
#         df.to_excel(response, index=False)
#         return response


    # from rest_framework.views import APIView
    # from rest_framework.response import Response
    # from rest_framework.permissions import IsAuthenticated
    # from django.db.models import Q
    # from django.utils.dateparse import parse_date
    # from django.http import HttpResponse
    # import pandas as pd
    # from datetime import date

    # from auth_system.permissions.token_valid import IsTokenValid

    # from kyc_api_gateway.models import (
    # KycMyServices,
    # VendorManagement,
    # ClientManagement,
    # UatNameMatchRequestLog,
    # UatPanRequestLog,
    # UatRcRequestLog,
    # UatAddressMatchRequestLog,
    # UatDrivingLicenseRequestLog,
    # UatPassportRequestLog,
    # UatBillRequestLog,
    # )

    # # Map service name to log table model

    # SERVICE_LOG_MAPPING = {
    # "PAN": UatPanRequestLog,
    # "BILL": UatBillRequestLog,
    # "VOTER": UatDrivingLicenseRequestLog,
    # "NAME": UatNameMatchRequestLog,
    # "RC": UatRcRequestLog,
    # "DRIVING": UatDrivingLicenseRequestLog,
    # "PASSPORT": UatPassportRequestLog,
    # "ADDRESS": UatAddressMatchRequestLog,
    # }

    # class KycDynamicReportAPIView(APIView):
    # permission_classes = [IsAuthenticated, IsTokenValid]

    # def post(self, request):
    #     data = request.data
    #     client_id = data.get("client_id")
    #     vendor_id = data.get("vendor_id")
    #     myservice_id = data.get("myservice_id")
    #     status_val = data.get("status")
    #     from_date = data.get("from_date")
    #     to_date = data.get("to_date")
    #     today_only = data.get("today", False)

    #     # Validate service
    #     my_service = KycMyServices.objects.filter(id=myservice_id).first()
    #     if not my_service:
    #         return Response({"success": False, "message": "Invalid service selected"}, status=400)

    #     log_model = SERVICE_LOG_MAPPING.get(my_service.name.upper())
    #     if not log_model:
    #         return Response({"success": False, "message": f"No log table mapped for {my_service.name}"}, status=400)

    #     # Build filters
    #     filters = Q()
    #     if today_only:
    #         filters &= Q(created_at__date=date.today())
    #     if from_date and to_date:
    #         from_date_parsed = parse_date(from_date)
    #         to_date_parsed = parse_date(to_date)
    #         if from_date_parsed and to_date_parsed:
    #             filters &= Q(created_at__date__range=[from_date_parsed, to_date_parsed])
    #     if client_id:
    #         filters &= Q(client_id=client_id)
    #     if vendor_id:
    #         filters &= Q(vendor_id=vendor_id)
    #     if status_val:
    #         filters &= Q(status__iexact=status_val)

    #     # Fetch logs
    #     logs_qs = log_model.objects.filter(filters).select_related("client", "vendor").order_by("-id")

    #     # Dynamically get all field names from model
    #     model_fields = [f.name for f in log_model._meta.fields]

    #     rows = []
    #     for log in logs_qs:
    #         row = {}
    #         for field in model_fields:
    #             value = getattr(log, field, None)
    #             if field in ["client", "vendor"]:
    #                 # Convert related fields to names
    #                 if value:
    #                     value = value.company_name if field == "client" else value.vendor_name
    #                 else:
    #                     value = ""
    #             elif hasattr(value, "strftime"):  # datetime fields formatting
    #                 value = value.strftime("%Y-%m-%d %H:%M:%S")
    #             row[field] = value
    #         rows.append(row)

    #     # Convert to DataFrame
    #     df = pd.DataFrame(rows)

    #     response = HttpResponse(content_type='application/vnd.ms-excel')
    #     response['Content-Disposition'] = f'attachment; filename="{my_service.name}_kyc_report.xlsx"'
    #     df.to_excel(response, index=False)
    #     return response

