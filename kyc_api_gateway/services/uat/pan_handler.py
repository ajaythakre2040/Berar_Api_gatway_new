import requests
from kyc_api_gateway.models import UatPanDetails
from kyc_api_gateway.utils.constants import VENDOR_SERVICE_ENDPOINTS, DEFAULT_COUNTRY
from decouple import config

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)

if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")

def build_vendor_request(vendor_name, request_data):
    if vendor_name == "karza":
        return {
            "pan":  request_data.get("pan") or request_data.get("pan"),
            "aadhaarLastFour": "",
            "dob": "",
            "name": "",
            "address": "",
            "getContactDetails": "Y",
            "PANStatus": "Y",
            "isSalaried": "Y",
            "isDirector": "Y",
            "isSoleProp": "Y",
            "consent": "Y",
        }
    elif vendor_name == "surepass":
        return {
            "id_number": request_data.get("pan")
        }
    return request_data

# def call_vendor_api_pan(vendor, request_data):
   
#     import requests
#     vendor_key = vendor.vendor_name.lower()
#     endpoint_path = VENDOR_SERVICE_ENDPOINTS.get(vendor_key)

#     if not endpoint_path:
#         print(f"[ERROR] Vendor '{vendor.vendor_name}' has no endpoint path configured.")
#         return None

#     base_url = vendor.end_point_uat
#     if not base_url:
#         print(f"[ERROR] Vendor '{vendor.vendor_name}' has no URL configured.")
#         return None

#     full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
#     print(f"[DEBUG] Full URL: {full_url}")

#     headers = {"Content-Type": "application/json"}
#     payload = build_vendor_request(vendor_key, request_data)

#     print(f"[DEBUG] Payload: {payload}")

#     if vendor_key == "karza":
#         headers["x-karza-key"] = vendor.uat_key

#     elif vendor_key == "surepass":
#         headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

#     try:
#         response = requests.post(full_url, json=payload, headers=headers, timeout=vendor.timeout or 30)
#         print(f"[DEBUG] Vendor '{vendor.vendor_name}' response status: {response.status_code}")
#         return response

#     except Exception as e:
#         print(f"[ERROR] API call failed for vendor '{vendor.vendor_name}': {str(e)}")
#         return None
    
def call_vendor_api(vendor, request_data):
   
    import requests
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url

    if not endpoint_path or not base_url:
        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": f"Vendor '{vendor.vendor_name}' not configured properly."
        }

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"

    headers = {"Content-Type": "application/json"}
    payload = build_vendor_request(vendor_key, request_data)


    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key

    elif vendor_key == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"
    
    try:
        response = requests.post(full_url, json=payload, headers=headers)
        response.raise_for_status()  # Will trigger HTTPError for 4xx/5xx
        # response = requests.post(full_url, json=payload, headers=headers, timeout=vendor.timeout or 30)
        # return response
    
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
def normalize_vendor_response(vendor_name, raw_data):
 
    result = raw_data.get("result") or raw_data.get("data") or {}
    if not result:
        return None

    if vendor_name.lower() == "karza":
        return {
            "request_id": raw_data.get("requestId"),
            "pan_number": result.get("pan"),
            "full_name": result.get("name"),
            "first_name": result.get("firstName"),
            "middle_name": result.get("middleName"),
            "last_name": result.get("lastName"),
            "dob": result.get("dob"),
            "gender": result.get("gender"),
            "phone_number": result.get("mobileNo"),
            "email": result.get("emailId"),
            "aadhaar_linked": result.get("aadhaarLinked"),
            "masked_aadhaar": result.get("masked_aadhaar"),
            "aadhaar_match": result.get("aadhaarMatch"),
            "pan_status": result.get("status"),
            "is_salaried": result.get("isSalaried"),
            "is_director": result.get("isDirector"),
            "is_sole_prop": result.get("isSoleProp"),
            "issue_date": result.get("issueDate"),
            "address": {
                "line_1": result.get("buildingName"),
                "line_2": result.get("locality"),
                "street_name": result.get("streetName"),
                "city": result.get("city"),
                "state": result.get("state"),
                "zip": result.get("pinCode"),
                "country": result.get("country"),
                "full": result.get("fullAddress"),
            },
        }

    if vendor_name.lower() == "surepass":
        split = result.get("full_name_split", [])
        return {
            "client_id": result.get("client_id"),
            "pan_number": result.get("pan_number"),
            "full_name": result.get("full_name"),
            "first_name": split[0] if len(split) > 0 else None,
            "middle_name": split[1] if len(split) > 1 else None,
            "last_name": split[2] if len(split) > 2 else None,
            "dob": result.get("dob") or result.get("input_dob"),
            "gender": "male" if str(result.get("gender", "")).lower().startswith("m") else "female",
            "phone_number": result.get("phone_number"),
            "email": result.get("email"),
            "aadhaar_linked": result.get("aadhaar_linked"),
            "masked_aadhaar": result.get("masked_aadhaar"),
            "dob_verified": result.get("dob_verified"),
            "dob_check": result.get("dob_check"),
            "category": result.get("category"),
            "less_info": result.get("less_info"),
            "address": result.get("address") or {},
        }

    return None


def save_pan_data(normalized, created_by):
   
    address = normalized.get("address", {})
    pan_obj = UatPanDetails.objects.create(
        request_id=normalized.get("request_id"),
        client_id=normalized.get("client_id"),
        pan_number=normalized.get("pan_number"),
        full_name=normalized.get("full_name"),
        first_name=normalized.get("first_name"),
        middle_name=normalized.get("middle_name"),
        last_name=normalized.get("last_name"),
        gender=normalized.get("gender"),
        dob=normalized.get("dob"),
        dob_verified=normalized.get("dob_verified"),
        dob_check=normalized.get("dob_check"),
        phone_number=normalized.get("phone_number"),
        email=normalized.get("email"),
        aadhaar_linked=normalized.get("aadhaar_linked"),
        masked_aadhaar=normalized.get("masked_aadhaar"),
        aadhaar_match=normalized.get("aadhaar_match"),
        pan_status=normalized.get("pan_status"),
        is_salaried=normalized.get("is_salaried"),
        is_director=normalized.get("is_director"),
        is_sole_prop=normalized.get("is_sole_prop"),
        issue_date=normalized.get("issue_date"),
        category=normalized.get("category"),
        less_info=normalized.get("less_info"),
        address_line_1=address.get("line_1"),
        address_line_2=address.get("line_2"),
        street_name=address.get("street_name"),
        city=address.get("city"),
        state=address.get("state"),
        pin_code=address.get("zip"),
        country=address.get("country") or DEFAULT_COUNTRY,
        full_address=address.get("full"),
        created_by=created_by,
    )
    return pan_obj

