import requests
from decouple import config
from kyc_api_gateway.models import UatRcDetails
from kyc_api_gateway.utils.constants import VENDOR_RC_SERVICE_ENDPOINTS

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")


def build_rc_request(vendor_name, request_data):
    if vendor_name.lower() == "karza":
     
     return {
            "registrationNumber": request_data.get("rc_number"),
            "consent": request_data.get("consent", "Y"),
            "partialEngine": "Y",
            "version": 3.1,
            "clientData": {"caseId": request_data.get("clientData", {}).get("caseId", "123456")},
        }

    elif vendor_name.lower() == "surepass":
        return {
            "id_number": request_data.get("rc_number")
        }

    return request_data

def call_rc_vendor_api(vendor, request_data):
    
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_RC_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url

    if not endpoint_path or not base_url:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": f"Vendor '{vendor.vendor_name}' not configured properly."
        }

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    payload = build_rc_request(vendor_key, request_data)

    print('RC Payload:', payload)
    print('RC URL:', full_url)

    headers = {"Content-Type": "application/json"}
    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key
    elif vendor_key == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

    try:
        response = requests.post(full_url, json=payload, headers=headers)
        response.raise_for_status()
        try:
            print("Handler Response:", response.json())
            return response.json()
        except ValueError:
            return {
                "http_error": True,
                "status_code": response.status_code,
                "vendor_response": response.text,
                "error_message": "Invalid JSON response"
            }

    except requests.HTTPError as e:
        try:
            error_content = response.json()
        except Exception:
            error_content = response.text
        return {
            "http_error": True,
            "status_code": response.status_code,
            "vendor_response": error_content,
            "error_message": str(e)
        }

    except Exception as e:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": str(e)
        }


def normalize_rc_response(vendor_name, raw_data):
    
    result = raw_data.get("result") or raw_data.get("data") or raw_data
    if not result:
        return None

    # Common normalization for both vendors
    normalized = {
        "client_id": result.get("client_id"),
        "rc_number": result.get("rc_number") or result.get("registrationNumber"),
        "fit_up_to": result.get("fitnessUpto") or result.get("fit_up_to"),
        "registration_date": result.get("registration_date") or result.get("registrationDate"),
        "owner_name": result.get("owner_name") or result.get("ownerName"),
        "father_name": result.get("father_name") or result.get("fatherName"),
        "present_address": result.get("present_address") or result.get("presentAddress"),
        "permanent_address": result.get("permanent_address") or result.get("permanentAddress"),
        "mobile_number": result.get("mobile_number") or result.get("rcMobileNo"),
        "vehicle_category": result.get("vehicle_category") or result.get("vehicleCategory"),
        "vehicle_category_description": result.get("vehicle_category_description") or result.get("vehicleClassDescription"),
        "vehicle_chasi_number": result.get("vehicle_chasi_number") or result.get("chassisNumber"),
        "vehicle_engine_number": result.get("vehicle_engine_number") or result.get("engineNumber"),
        "maker_description": result.get("maker_description") or result.get("makerDescription"),
        "maker_model": result.get("maker_model") or result.get("makerModel"),
        "body_type": result.get("body_type") or result.get("bodyTypeDescription"),
        "fuel_type": result.get("fuel_type") or result.get("fuelDescription"),
        "color": result.get("color"),
        "norms_type": result.get("norms_type") or result.get("normsDescription"),
        "financer": result.get("financer") or result.get("financier"),
        "insurance_company": result.get("insurance_company") or result.get("insuranceCompany"),
        "insurance_policy_number": result.get("insurance_policy_number") or result.get("insurancePolicyNumber"),
        "insurance_upto": result.get("insurance_upto") or result.get("insuranceUpto"),
        "registered_at": result.get("registered_at") or result.get("registeredAt"),
        "tax_paid_upto": result.get("tax_paid_upto") or result.get("taxPaidUpto"),
        "cubic_capacity": result.get("cubic_capacity") or result.get("cubicCapacity"),
        "vehicle_gross_weight": result.get("vehicle_gross_weight") or result.get("grossVehicleWeight"),
        "unladen_weight": result.get("unladen_weight") or result.get("unladenWeight"),
        "no_cylinders": result.get("no_cylinders") or result.get("numberOfCylinders"),
        "seat_capacity": result.get("seat_capacity") or result.get("seatingCapacity"),
        "sleeper_capacity": result.get("sleeper_capacity") or result.get("sleeperCapacity"),
        "standing_capacity": result.get("standing_capacity") or result.get("standingCapacity"),
        "wheelbase": result.get("wheelbase"),
        "manufactured_month_year": result.get("manufacturedMonthYear") or result.get("manufacturing_date"),
        "puc_expiry_date": result.get("pucExpiryDate") or result.get("pucc_upto"),
        "pucc_number": result.get("pucNumber") or result.get("pucc_number"),
        "blacklist_status": result.get("blacklist_status") or result.get("blackListStatus"),
        "blacklist_info": result.get("blacklist_info") or result.get("blackListInfo") or {},
        "noc_details": result.get("noc_details") or result.get("nocDetails"),
        "rc_status": result.get("rc_status") or result.get("rcStatus"),
        "less_info": result.get("less_info", False),
        "response_metadata": result.get("response_metadata") or {},
    }

    return normalized

def save_rc_data(normalized, created_by):
 
    if not normalized or not normalized.get("rc_number"):
        raise ValueError("RC number missing in normalized data")

    rc_obj, created = UatRcDetails.objects.update_or_create(
        rc_number=normalized.get("rc_number"),
        defaults={**normalized, "created_by": created_by},
    )

    print("RC Data Saved:", rc_obj.rc_number, "| Created:", created)
    return rc_obj