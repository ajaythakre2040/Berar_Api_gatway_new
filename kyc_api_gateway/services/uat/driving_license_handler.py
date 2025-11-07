import requests
from decimal import Decimal
from decouple import config
from kyc_api_gateway.models import UatDrivingLicense
from kyc_api_gateway.utils.constants import VENDOR_DRIVING_LICENSE_ENDPOINTS
from datetime import datetime

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in environment variables.")


def format_dob_for_vendor(vendor_name, dob_str):
    if not dob_str:
        return None
    try:
        dob_obj = datetime.strptime(dob_str, "%d-%m-%Y")
        if vendor_name.lower() == "surepass":
            return dob_obj.strftime("%Y-%m-%d")
        return dob_str
    except Exception:
        return dob_str


def build_dl_request_uat(vendor_name, request_data):
    vendor_name = vendor_name.lower()
    
    dob = format_dob_for_vendor(vendor_name, request_data.get("dob"))

    if vendor_name == "karza":
        return {
            "dlNo": request_data.get("license_no") or request_data.get("dlNo"),
            "dob": dob,
            "additionalDetails": True,
            "consent": "Y",
            "clientData": {"caseId": "123456"},
        }

    elif vendor_name == "surepass":
        return {
            "id_number": request_data.get("license_no") or request_data.get("dlNo"),
            "dob": dob,
        }

    return None



# def call_vendor_api_uat(vendor, request_data):
    
#     vendor_key = vendor.vendor_name.lower()
#     endpoint_path = VENDOR_DRIVING_LICENSE_ENDPOINTS.get(vendor_key)

#     if not endpoint_path:
#         print(f"[ERROR] No endpoint found for vendor: {vendor.vendor_name}")
#         return None

#     base_url = vendor.end_point_uat
#     full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"

#     headers = {"Content-Type": "application/json"}
#     if vendor_key == "karza":

#         headers["x-karza-key"] = vendor.uat_key

#     elif vendor_key == "surepass":
#         headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

#     payload = build_dl_request_uat(vendor_key, request_data)

#     try:
#         response = requests.post(full_url, json=payload, headers=headers, timeout=vendor.timeout or 30)

#         # print(f"[INFO] {vendor.vendor_name} request sent to {full_url} with payload: {payload}")
#         # print(f"[INFO] {vendor.vendor_name} response status: {response.status_code}, response body: {response.text}")
#         # print(response.json())

#         return response
#     except Exception as e:
#         print(f"[ERROR] {vendor.vendor_name} request failed: {str(e)}")
#         return None

def call_vendor_api_uat(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_DRIVING_LICENSE_ENDPOINTS.get(vendor_key)

    if not endpoint_path:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": f"No endpoint found for vendor {vendor.vendor_name}"
        }

    base_url = vendor.uat_base_url
    if not base_url:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": f"No base URL configured for vendor {vendor.vendor_name}"
        }

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    headers = {"Content-Type": "application/json"}

    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key
    elif vendor_key == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

    payload = build_dl_request_uat(vendor_key, request_data)

    try:
        # response = requests.post(full_url, json=payload, headers=headers, timeout=vendor.timeout or 30)
        response = requests.post(full_url, json=payload, headers=headers)

        # ✅ Handle 4xx/5xx responses gracefully
        if response.status_code >= 400:
            try:
                error_json = response.json()
            except Exception:
                error_json = response.text

            return {
                "http_error": True,
                "status_code": response.status_code,
                "vendor_response": error_json,
                "error_message": f"Vendor {vendor.vendor_name} returned error {response.status_code}"
            }

        try:
            return response.json()
        except Exception:
            return {
                "http_error": True,
                "status_code": response.status_code,
                "vendor_response": response.text,
                "error_message": "Invalid JSON from vendor"
            }

    except Exception as e:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": f"{vendor.vendor_name} request failed: {str(e)}"
        }


def normalize_vendor_response(vendor_name, raw_data, request_data=None):
    vendor_name = vendor_name.lower()
    
    if vendor_name == "karza":
        result = raw_data.get("result", {}) or {}
        validity = result.get("validity", {}) or {}
        address_list = result.get("address", []) or []
        photo = result.get("img")
        cov_details = result.get("covDetails", []) 

        permanent_address = ""
        if isinstance(address_list, list) and address_list:
            for addr in address_list:
                if addr.get("type", "").lower() == "permanent":
                    permanent_address = addr.get("completeAddress", "")
                    break
            if not permanent_address:
                permanent_address = address_list[0].get("completeAddress", "")

        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, "%d-%m-%Y").date()
            except:
                return None

        non_transport_validity = parse_date(validity.get("nonTransport"))
        transport_validity = parse_date(validity.get("transport"))
        issue_date = parse_date(result.get("issueDate"))
        dob = parse_date(result.get("dob"))

        return {
            "client_id": raw_data.get("requestId"),
            "request_id": raw_data.get("requestId"),
            "dl_number": result.get("dlNumber") or (request_data.get("license_no") if request_data else None),
            "dob": dob or (parse_date(request_data.get("dob")) if request_data else None),
            "name": result.get("name"),
            "father_name": result.get("father/husband"),
            "issue_date": issue_date,
            "valid_till": non_transport_validity or transport_validity,
            "non_transport_validity": non_transport_validity,
            "transport_validity": transport_validity,
            "address": permanent_address,
            "state": (address_list[0].get("state") if address_list else None),
            "rto_code": None, 
            "blood_group": result.get("bloodGroup"),
            "photo": photo,
            "signature": None,
            "is_verified": result.get("status") == "ACTIVE",
            "vendor_name": "karza",
            "dl_status": result.get("status"),
            "issuing_authority": result.get("endorsementAndHazardousDetails", {}).get("initialIssuingOffice"),
            "full_response": raw_data,
        }

    elif vendor_name == "surepass":
        data = raw_data.get("data", {})
        return {
            "client_id": data.get("client_id"),
            "request_id": raw_data.get("request_id") or data.get("client_id"),
            "dl_number": data.get("license_number"),
            "name": data.get("name"),
            "father_name": data.get("father_or_husband_name"),
            "dob": data.get("dob"),
            "issue_date": data.get("doi"),
            "valid_till": data.get("doe"),
            "non_transport_validity": data.get("transport_doi"),
            "transport_validity": data.get("transport_doe"),
            "address": data.get("permanent_address"),
            "state": data.get("state"),
            "rto_code": data.get("ola_code"),
            "issuing_authority": data.get("ola_name"),
            "blood_group": data.get("blood_group"),
            "photo": data.get("profile_image"),
            "dl_status": data.get("dl_status") or "Active",
            "vendor_name": "surepass",
            "status": data.get("status"),
        }

    return None

def save_uat(normalized, created_by, vendor_name=None, full_response=None):
    dl_obj = UatDrivingLicense.objects.create(
        client_id=normalized.get("client_id"),
        request_id=normalized.get("request_id"),
        dl_number=normalized.get("dl_number"),
        name=normalized.get("name"),
        father_name=normalized.get("father_name"),
        dob=normalized.get("dob"),
        issue_date=normalized.get("issue_date"),
        valid_till=normalized.get("valid_till"),
        non_transport_validity=normalized.get("non_transport_validity"),
        transport_validity=normalized.get("transport_validity"),
        address=normalized.get("address"),
        state=normalized.get("state"),
        rto_code=normalized.get("rto_code"),
        blood_group=normalized.get("blood_group"),
        dl_status=normalized.get("dl_status"),
        issuing_authority=normalized.get("issuing_authority"),
        photo=normalized.get("photo"),
        vendor_name=vendor_name,
        full_response=full_response,
        created_by=created_by,
    )
    return dl_obj

def sanitize_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def call_dynamic_vendor_api(url, request_data):
    headers = {"Content-Type": "application/json"}
    vendor_name = request_data.get("vendor")
    header_key_name = request_data.get("header_key_name")
    api_key = request_data.get("api_key")
   
    if vendor_name == "karza":
        headers["x-karza-key"] = api_key
    elif vendor_name == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"
    if header_key_name and api_key:
        headers[header_key_name] = api_key
    payload = build_dl_request_uat(vendor_name, request_data)
    try:
        response = requests.post(url, json=payload, headers=headers)
       
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {
                "http_error": True,
                "status_code": response.status_code,
                "vendor_response": response.text,
                "error_message": "Invalid JSON response",
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
            "error_message": str(e),
        }
    except Exception as e:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": str(e),
        }
