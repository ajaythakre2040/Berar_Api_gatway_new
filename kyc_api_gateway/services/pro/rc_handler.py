import requests
from decouple import config
from kyc_api_gateway.models import ProRcDetails
from kyc_api_gateway.utils.constants import VENDOR_RC_SERVICE_ENDPOINTS

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")



def build_rc_request(vendor_name, request_data):
    if vendor_name.lower() == "karza":

     return {
            "reg_no": request_data.get("rc_number"),
            "consent": request_data.get("consent", "Y"),
            "clientData": {"caseId": request_data.get("clientData", {}).get("caseId", "123456")},
        }

    elif vendor_name.lower() == "surepass":
        # return {"id_number": request_data.get("rc_number")}
        return {
            "id_number": request_data.get("rc_number")
        }


    return request_data



# def call_vendor_api(vendor, request_data):

#     vendor_key = vendor.vendor_name.lower()
#     endpoint_path = VENDOR_RC_SERVICE_ENDPOINTS.get(vendor_key)
    
#     if not endpoint_path:
#         print(f"[ERROR] Vendor '{vendor.vendor_name}' has no endpoint")
#         return None

#     base_url = vendor.end_point_production
#     if not base_url:
#         print(f"[ERROR] Vendor '{vendor.vendor_name}' has no base URL for")
#         return None

#     full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"

#     payload = build_rc_request(vendor_key, request_data)

#     headers = {"Content-Type": "application/json"}

#     if vendor_key == "karza":
#         headers["x-karza-key"] = vendor.production_key
#     elif vendor_key == "surepass":
#         headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

#     try:
#         response = requests.post(full_url, json=payload, headers=headers, timeout=vendor.timeout or 30)
#         response.raise_for_status()
#         try:
#             return response.json()  
#         except ValueError:
#             print(f"[ERROR] Vendor '{vendor.vendor_name}' returned invalid JSON: {response.text}")
#             return None
#     except Exception as e:
#         print(f"[ERROR] RC API call failed ({vendor.vendor_name}): {str(e)}")
#         return None

def call_rc_vendor_api(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_RC_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.prod_base_url

    if not endpoint_path or not base_url:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": f"Vendor '{vendor.vendor_name}' not configured properly."
        }

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    payload = build_rc_request(vendor_key, request_data)

    headers = {"Content-Type": "application/json"}
    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.prod_api_key
    elif vendor_key == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

    try:
        response = requests.post(full_url, json=payload, headers=headers)
        response.raise_for_status()  # Will trigger HTTPError for 4xx/5xx

        try:
            return response.json()
        except ValueError:
            return {
                "http_error": True,
                "status_code": response.status_code,
                "vendor_response": response.text,
                "error_message": "Invalid JSON response"
            }

    except requests.HTTPError as e:
        # Capture 400/403/500 error details for logging
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



def normalize_response(vendor_name, raw_data):
    if not isinstance(raw_data, dict):
        print(f"[ERROR] normalize_rc_response received invalid data: {raw_data}")
        return None

    vendor_key = vendor_name.lower()

    if vendor_key == "karza":
        result = raw_data.get("result", {})
        return {
            "vendor": "karza",
            "client_id": raw_data.get("clientData", {}).get("caseId"),
            "rc_number": result.get("rc_regn_no"),
            "owner_name": result.get("rc_owner_name"),
            "father_name": result.get("rc_f_name"),
            "present_address": result.get("rc_present_address"),
            "mobile_number": result.get("rc_mobile_no"),
            "maker_model": result.get("rc_maker_model"),
            "maker_description": result.get("rc_maker_desc"),
            "body_type": result.get("rc_body_type_desc"),
            "fuel_type": result.get("rc_fuel_desc"),
            "color": result.get("rc_color"),
            "insurance_company": result.get("rc_insurance_comp"),
            "insurance_policy_number": result.get("rc_insurance_policy_no"),
            "insurance_upto": result.get("rc_insurance_upto"),
            "fit_upto": result.get("rc_fit_upto"),
            "registration_date": result.get("rc_regn_dt"),
            "registered_at": result.get("rc_registered_at"),
            "tax_upto": result.get("rc_tax_upto"),
            "financer": result.get("rc_financer"),
            "rc_status": result.get("rc_status_as_on"),
        }

    elif vendor_key == "surepass":
        d = raw_data.get("data", {})
        return {
            "vendor": "surepass",
            "client_id": d.get("client_id"),
            "rc_number": d.get("rc_number"),
            "owner_name": d.get("owner_name"),
            "father_name": d.get("father_name"),
            "present_address": d.get("present_address"),
            "permanent_address": d.get("permanent_address"),
            "mobile_number": d.get("mobile_number"),
            "maker_model": d.get("maker_model"),
            "maker_description": d.get("maker_description"),
            "body_type": d.get("body_type"),
            "fuel_type": d.get("fuel_type"),
            "color": d.get("color"),
            "insurance_company": d.get("insurance_company"),
            "insurance_policy_number": d.get("insurance_policy_number"),
            "insurance_upto": d.get("insurance_upto"),
            "fit_upto": d.get("fit_up_to"),
            "registration_date": d.get("registration_date"),
            "registered_at": d.get("registered_at"),
            "tax_upto": d.get("tax_upto"),
            "cubic_capacity": d.get("cubic_capacity"),
            "vehicle_gross_weight": d.get("vehicle_gross_weight"),
            "seat_capacity": d.get("seat_capacity"),
            "unladen_weight": d.get("unladen_weight"),
            "rc_status": d.get("rc_status"),
        }


def save_data(normalized, created_by):
    if not normalized:
        print("[ERROR] Cannot save RC data: normalized is None")
        return None

    rc_fields = [f.name for f in ProRcDetails._meta.get_fields()]

    filtered_data = {k: v for k, v in normalized.items() if k in rc_fields}

    filtered_data["created_by"] = created_by

    try:
        return ProRcDetails.objects.create(**filtered_data)
    except Exception as e:
        print(f"[ERROR] Failed saving RCDetails: {e}")
        return None

