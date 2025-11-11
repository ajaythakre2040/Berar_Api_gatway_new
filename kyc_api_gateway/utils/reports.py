# kyc_api_gateway/utils/reports.py

from django.utils.dateparse import parse_date
from constant import KYC_MY_SERVICES
from kyc_api_gateway.models import (
    UatPanRequestLog, UatBillRequestLog, UatVoterRequestLog,
    UatNameMatchRequestLog, UatRcRequestLog,
    UatDrivingLicenseRequestLog, UatPassportRequestLog,
    UatAddressMatchRequestLog,KycClientServicesManagement
)

def get_filtered_queryset(data):
    
    myservice_id = data.get("myservice_id")
    vendor_name = data.get("vendor_name")
    status_code = data.get("status_code")
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    client_id = data.get("client_id")

    if client_id:
        allowed_services = KycClientServicesManagement.objects.filter(
            client_id=client_id,
            status=True
        ).values_list('myservice_id', flat=True)

    if myservice_id and int(myservice_id) not in allowed_services:
        return None, None, "Unauthorized access to the requested service"
    
    service_map = {
        KYC_MY_SERVICES.get("PAN"): (UatPanRequestLog, "PAN"),
        KYC_MY_SERVICES.get("BILL"): (UatBillRequestLog, "BILL"),
        KYC_MY_SERVICES.get("VOTER"): (UatVoterRequestLog, "VOTER"),
        KYC_MY_SERVICES.get("NAME"): (UatNameMatchRequestLog, "NAME"),
        KYC_MY_SERVICES.get("RC"): (UatRcRequestLog, "RC"),
        KYC_MY_SERVICES.get("DRIVING"): (UatDrivingLicenseRequestLog, "DRIVING"),
        KYC_MY_SERVICES.get("PASSPORT"): (UatPassportRequestLog, "PASSPORT"),
        KYC_MY_SERVICES.get("ADDRESS"): (UatAddressMatchRequestLog, "ADDRESS"),
    }

    model_info = service_map.get(myservice_id)
    if not model_info:
        return None, None, "Unsupported myservice_id"

    model, service_name = model_info
    queryset = model.objects.all().order_by("-created_at")

    if vendor_name:
        queryset = queryset.filter(vendor__iexact=vendor_name.strip())

    if status_code:
        queryset = queryset.filter(status_code=status_code)

    if client_id:
        queryset = queryset.filter(created_by=client_id)

    if from_date or to_date:
        from_date_parsed = parse_date(from_date) if from_date else None
        to_date_parsed = parse_date(to_date) if to_date else None
        if from_date_parsed and to_date_parsed:
            if from_date_parsed > to_date_parsed:
                from_date_parsed, to_date_parsed = to_date_parsed, from_date_parsed
            queryset = queryset.filter(created_at__date__range=[from_date_parsed, to_date_parsed])
        elif from_date_parsed:
            queryset = queryset.filter(created_at__date__gte=from_date_parsed)
        elif to_date_parsed:
            queryset = queryset.filter(created_at__date__lte=to_date_parsed)

    return queryset, service_name, None
