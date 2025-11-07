import requests
from decouple import config
from auth_system.models.user import TblUser
from kyc_api_gateway.models import UatPassportDetails
from kyc_api_gateway.utils.constants import (
    VENDOR_PASSPORT_SERVICE_ENDPOINTS,
)  # new constant mapping like name
from decimal import Decimal
import re
from datetime import datetime

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")


def build_passport_request_uat(vendor_name, request_data):
    vendor_key = vendor_name.lower()

    dob_input = request_data.get("dob")
    formatted_dob = None

    if dob_input:
        try:
            if "-" in dob_input:
                dob_obj = datetime.strptime(dob_input, "%Y-%m-%d")
            elif "/" in dob_input:
                dob_obj = datetime.strptime(dob_input, "%d/%m/%Y")
            else:
                dob_obj = None

            if dob_obj:
                if vendor_key == "karza":
                    formatted_dob = dob_obj.strftime("%d/%m/%Y")
                elif vendor_key == "surepass":
                    formatted_dob = dob_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"[WARN] DOB format invalid: {dob_input} ({e})")

    if vendor_key == "karza":


        return {
            "consent": request_data.get("consent", "y"),
            "fileNo": request_data.get("file_number"),
            "dob": formatted_dob or request_data.get("dob"),
            "passportNo": request_data.get("passportNo"),
            "doi": request_data.get("doi"),
            "name": request_data.get("name"),
            "clientData": request_data.get("clientData", {"caseId": "123456"}),
        }

    elif vendor_key == "surepass":
        return {
            "id_number": request_data.get("file_number"),
            "dob": formatted_dob or request_data.get("dob"),
        }

    return request_data


def call_vendor_api_uat(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_PASSPORT_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url

    if not endpoint_path or not base_url:
        print(f"[ERROR] Vendor '{vendor.vendor_name}' not configured properly.")
        return None

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    payload = build_passport_request_uat(vendor_key, request_data)

    headers = {"Content-Type": "application/json"}
    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key
    elif vendor_key == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"  # Bearer token


    print("\n--- Calling Vendor UAT Name API ---")
    print("URL:", full_url)
    print("Headers:", headers)
    print("Payload:", payload)

    try:
        response = requests.post(full_url, json=payload, headers=headers)
        response.raise_for_status()

        
        print("\n--- Vendor UAT Name API Response ---")
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())

        return response.json()

    except requests.HTTPError as e:
        try:
            error_content = response.json()
        except Exception:
            error_content = response.text


        print("Error Message:", str(e))
        # print("Error Content:", error_content)

        return {
            "http_error": True,
            "status_code": response.status_code,
            "vendor_response": error_content,
            "error_message": str(e),
        }

    except Exception as e:
        print("Error Message:", str(e))

        return {
            "http_error": True,
            "status_code": None,
            "vendor_response": None,
            "error_message": str(e),
        }


def normalize_vendor_response(vendor_name, raw_data, request_data):
    vendor_name = vendor_name.lower()
    

    print("\n--- Normalizing Vendor Response ---")
    print("Vendor Name:", vendor_name)
    print("Raw Data:", raw_data)

    if vendor_name == "surepass":
        result = raw_data.get("data", {})
        if not result:
            return {"error": "Missing or invalid 'data' in Surepass response"}

        full_name = result.get("full_name", "")
        surname = full_name.split()[-1] if full_name else None
        status = result.get("status", "")

        date_of_issue = extract_date_from_text(status) if status else None

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

        print("\n--- Karza Raw Response ---")
        print(raw_data)
        
        result = raw_data.get("result", {})
        if not result:
            return {"error": "Missing or invalid 'data' in Karza response"}

        full_name = result.get("full_name", "")
        surname = full_name.split()[-1] if full_name else None
        status = result.get("status", "")

        date_of_issue = extract_date_from_text(status) if status else None

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

    return {"error": "Unknown vendor or response format"}


def extract_date_from_text(text):
    """Extract dispatched date from text like 'dispatched on 26/09/2024'"""
    if not text:
        return None
    match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    return match.group(1) if match else None


def convert_date_format_to_ddmmyyyy(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. It should be in YYYY-MM-DD format.")


def convert_to_yyyy_mm_dd(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. It should be in DD/MM/YYYY format.")



def save_verification(normalized, created_by_id, vendor):
    # Ensure the date fields exist in normalized data and convert them to correct formats
    date_of_issue = normalized.get("date_of_issue")
    date_of_application = normalized.get("date_of_application")

    # Convert date_of_issue to YYYY-MM-DD format
    if date_of_issue:
        normalized["date_of_issue"] = convert_to_yyyy_mm_dd(date_of_issue)
    else:
        raise ValueError("Date of issue is missing or invalid.")

    # Ensure date_of_application is in the correct YYYY-MM-DD format
    if date_of_application:
        # If the date is already in the expected format (YYYY-MM-DD), do nothing
        try:
            # Check if the date is in the correct format
            datetime.strptime(date_of_application, "%Y-%m-%d")
        except ValueError:
            # If it's not in the correct format, convert it
            normalized["date_of_application"] = convert_to_yyyy_mm_dd(
                date_of_application
            )
    else:
        raise ValueError("Date of application is missing or invalid.")

    # Ensure created_by is a TblUser instance (fetching from ID)
    try:
        created_by = TblUser.objects.get(id=created_by_id)
    except TblUser.DoesNotExist:
        raise ValueError(f"User with ID {created_by_id} does not exist.")

    passport = UatPassportDetails.objects.create(
        client_id=normalized.get("client_id"),
        request_id=normalized.get("request_id"),
        passport_number=normalized.get("passport_number"),
        file_number=normalized.get("file_number"),
        full_name=normalized.get("full_name"),
        surname=normalized.get("surname"),
        dob=normalized.get("dob"),
        date_of_issue=normalized.get("date_of_issue"),  # None is fine
        date_of_application=normalized.get("date_of_application"),
        application_type=normalized.get("application_type"),
        status_text=normalized.get("status_text"),
        vendor=vendor.vendor_name,
        created_by=created_by,  # Pass the TblUser instance
    )

    # return passport_obj

# def save_verification(normalized, created_by, vendor):
#     passport_obj = UatPassportDetails.objects.create(
#         client_id=normalized.get("client_id"),
#         request_id=normalized.get("request_id"),
#         passport_number=normalized.get("passport_number"),
#         file_number=normalized.get("file_number"),
#         full_name=normalized.get("full_name"),
#         surname=normalized.get("surname"),
#         dob=normalized.get("dob"),
#         date_of_issue=normalized.get("date_of_issue"),
#         date_of_application=normalized.get("date_of_application"),
#         application_type=normalized.get("application_type"),
#         status_text=normalized.get("status_text"),
#         vendor=vendor.vendor_name,
#         created_by=created_by,
#     )
#     return passport_obj


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
