import requests
from decouple import config
from kyc_api_gateway.utils.constants import (
    VENDOR_PASSPORT_SERVICE_ENDPOINTS,
)  
import re
from datetime import datetime

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")

from datetime import datetime

def build_passport_request_uat(vendor_name, request_data):
    vendor_key = vendor_name.lower()
    dob_input = request_data.get("dob")

    dob_obj = None
    if dob_input:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                dob_obj = datetime.strptime(dob_input, fmt)
                break
            except ValueError:
                continue

    formatted_dob_karza = dob_obj.strftime("%d/%m/%Y") if dob_obj else dob_input
    formatted_dob_surepass = dob_obj.strftime("%Y-%m-%d") if dob_obj else dob_input

    # --- Karza Vendor ---
    if vendor_key == "karza":
        payload = {
            "consent": request_data.get("consent", "y"),
            "fileNo": request_data.get("fileNo") or request_data.get("file_number"),
            "dob": formatted_dob_karza,
            "clientData": request_data.get("clientData", {"caseId": "123456"}),
        }

        for key in ["passportNo", "doi", "name"]:
            if request_data.get(key):
                payload[key] = request_data[key]

        return payload

    elif vendor_key == "surepass":
        return {
            "id_number": request_data.get("file_number"),
            "dob": formatted_dob_surepass, 
        }

    return request_data

def call_vendor_api_uat(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_PASSPORT_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url

    if not endpoint_path or not base_url:
        return {
            "http_error": True,
            "error_message": f"Vendor '{vendor.vendor_name}' not configured properly."
        }

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    payload = build_passport_request_uat(vendor_key, request_data)

    headers = {"Content-Type": "application/json"}
    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key
    elif vendor_key == "surepass" and SUREPASS_TOKEN:
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

    try:
        response = requests.post(full_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status() 

        return response.json()

    except requests.exceptions.Timeout:
        return {
            "http_error": True,
            "error_message": "Vendor API request timed out."
        }

    except requests.exceptions.HTTPError as e:
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


from datetime import datetime
import re

def normalize_vendor_response(vendor_name, raw_data, request_data):
    vendor_name = vendor_name.lower()

    if vendor_name == "surepass":
        result = raw_data.get("data", {})
        if not result:
            return {"error": "Missing or invalid 'data' in Surepass response"}

        full_name = result.get("full_name", "")
        surname = full_name.split()[-1] if full_name else None
        status = result.get("status", "")
        date_of_issue = extract_date_from_text(status) if status else None

        if date_of_issue:
            try:
                date_of_issue = datetime.strptime(date_of_issue, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                date_of_issue = None

        return {
            "client_id": result.get("client_id", ""),
            "request_id": raw_data.get("requestId", ""),
            "passport_number": result.get("passport_number", ""),
            "file_number": result.get("file_number", ""),
            "full_name": full_name,
            "surname": surname,
            "dob": result.get("dob", ""),
            "date_of_application": result.get("date_of_application", ""),
            "date_of_issue": date_of_issue, 
            "application_type": result.get("application_type", ""),
            "status_text": status,
        }

    elif vendor_name == "karza":
        result = raw_data.get("result", {})
        if not result:
            return {"error": "Missing or invalid 'data' in Karza response"}

        name_data = result.get("name", {})
        passport_data = result.get("passportNumber", {})
        issue_data = result.get("dateOfIssue", {})

        def safe_convert(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                return None

        return {
            "client_id": raw_data.get("clientData", {}).get("caseId", ""),
            "request_id": raw_data.get("requestId", ""),
            "passport_number": passport_data.get("passportNumberFromSource", ""),
            "file_number": request_data.get("file_number", ""),
            "full_name": name_data.get("nameFromPassport", ""),
            "surname": name_data.get("surnameFromPassport", ""),
            "dob": safe_convert(request_data.get("dob")),
            "date_of_application": safe_convert(result.get("applicationDate")),
            "date_of_issue": safe_convert(issue_data.get("dispatchedOnFromSource")),
            "application_type": result.get("typeOfApplication", ""),
            "status_text": str(raw_data.get("statusCode", "")),
        }

    return {"error": "Unknown vendor or response format"}


def extract_date_from_text(text):
    if not text:
        return None
    match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    return match.group(1) if match else None


def extract_date_from_text(text):
    if not text:
        return None
    match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    return match.group(1) if match else None

def save_verification(normalized):
  
    from kyc_api_gateway.models import UatPassportDetails
    if "error" in normalized:
        raise ValueError(normalized["error"])
    passport = UatPassportDetails.objects.create(
        client_id=normalized.get("client_id"),
        request_id=normalized.get("request_id"),
        passport_number=normalized.get("passport_number"),
        file_number=normalized.get("file_number"),
        full_name=normalized.get("full_name"),
        surname=normalized.get("surname"),
        dob=normalized.get("dob"),
        date_of_issue=normalized.get("date_of_issue"),  
        date_of_application=normalized.get("date_of_application"),
        application_type=normalized.get("application_type"),
        status_text=normalized.get("status_text"),
    )
    return passport


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
    payload = build_passport_request_uat(vendor_name, request_data)
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
