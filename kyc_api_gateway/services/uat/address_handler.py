import requests
from decimal import Decimal
from decouple import config
from kyc_api_gateway.models import UatAddressMatch
from kyc_api_gateway.utils.constants import VENDOR_ADDRESS_SERVICE_ENDPOINTS

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")


# def build_address_request(vendor_name, request_data):
#     vendor_key = vendor_name.lower()

#     address1 = request_data.get("address1", "").strip()
#     address2 = request_data.get("address2", "").strip()

#     if vendor_key == "karza":
#         return {
#             "address1": address1,
#             "address2": address2,
#             "clientData": {"caseId": request_data.get("case_id", "123456")},
#         }

#     elif vendor_key == "surepass":
#         full_address = address1
#         if address2:
#             full_address = f"{address1} {address2}".strip()

#         return {"address": full_address}

#     return request_data
def build_address_request(vendor_name, request_data):
    vendor_key = vendor_name.lower()

    address1 = request_data.get("address1", "").strip()
    address2 = request_data.get("address2", "").strip()

    if vendor_key == "karza":
        return {
            "address1": address1,
            "address2": address2,
            "clientData": {"caseId": request_data.get("case_id", "123456")},
        }

    elif vendor_key == "internal":   
        return {
            "address1": address1,
            "address2": address2,
            "client_id": request_data.get("client_id"),
        }

    elif vendor_key == "surepass":
        full_address = address1
        if address2:
            full_address = f"{address1} {address2}".strip()
        return {"address": full_address}

    return request_data


def call_vendor_api(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_ADDRESS_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url

    if not endpoint_path or not base_url:
        return None

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    payload = build_address_request(vendor_key, request_data)

    headers = {"Content-Type": "application/json"}
    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key
    elif vendor_key == "internal":
        headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(full_url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

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


def sanitize_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def normalize_vendor_response(vendor_name, raw_data, request_data):
    vendor_name = vendor_name.lower()

    if vendor_name == "karza":
        result = raw_data.get("result", {})
        return {
            "client_id": raw_data.get("requestId"),
            "request_id": raw_data.get("requestId"),
            "address1": request_data.get("address1") if request_data else None,
            "address2": request_data.get("address2") if request_data else None,
            "match_score": result.get("score"),
            "match_status": result.get("match"),
            "status_code": raw_data.get("statusCode"),
            "vendor_response": raw_data,
            "district": result.get("address1", {}).get("district"),
            "state": result.get("address1", {}).get("state"),
            "locality": result.get("address1", {}).get("locality"),
        }

       
    elif vendor_name == "internal":
        return {
            "client_id": raw_data.get("client_id"),
            "request_id": raw_data.get("request_id"),
            "address1": request_data.get("address1") if request_data else None,
            "address2": request_data.get("address2") if request_data else None,
            "match_score": raw_data.get("score"),
            "match_status": raw_data.get("match"),
            "status_code": raw_data.get("status_code"),
            "vendor_response": raw_data,
            "district": raw_data.get("district"),
            "state": raw_data.get("state"),
            "locality": raw_data.get("locality"),
            "pincode": raw_data.get("pincode"),
        }


    return None


def save_address_match(normalized, created_by):
    match_obj = UatAddressMatch.objects.create(
        client_id=normalized.get("client_id"),
        request_id=normalized.get("request_id"),
        address1=normalized.get("address1"),
        address2=normalized.get("address2"),
        score=normalized.get("match_score"),
        match=normalized.get("match_status"),
        success=True,
        status_code=str(normalized.get("status_code", "")),
        message=normalized.get("message"),
        house=normalized.get("house"),
        locality=normalized.get("locality"),
        street=normalized.get("street"),
        district=normalized.get("district"),
        city=normalized.get("city"),
        state=normalized.get("state"),
        pincode=normalized.get("pincode"),
        vendor_response=normalized.get("vendor_response"),
        created_by=created_by,
    )
    return match_obj


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
    payload = build_address_request(vendor_name, request_data)
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
