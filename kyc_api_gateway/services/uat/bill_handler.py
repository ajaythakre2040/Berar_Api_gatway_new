import requests
from decimal import Decimal
from decouple import config
from kyc_api_gateway.models import UatElectricityBill
from kyc_api_gateway.utils.constants import VENDOR_BILL_SERVICE_ENDPOINTS


SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")


def build_vendor_request(vendor_name, request_data):
 
    vendor_key = vendor_name.lower()
    normalized_payload = None 

    if vendor_key == "karza":
        normalized_payload = {
            "consumer_id": request_data.get("consumer_id"),
            "service_provider": request_data.get("service_provider"),
            "district": request_data.get("district") or "",
            "regMobileNo": request_data.get("regMobileNo") or "",
            "consent": "Y",
            "clientData": {"caseId": request_data.get("caseId") or "123456"},
        }

    elif vendor_key == "surepass":
        normalized_payload = {
            "id_number": request_data.get("consumer_id"),
            "operator_code": request_data.get("service_provider"),
        }

    else:
        normalized_payload = request_data

    print(f"[DEBUG] Final payload for vendor '{vendor_name}': {normalized_payload}")

    return normalized_payload


def call_vendor_api_uat(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_BILL_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url

    if not endpoint_path or not base_url:
        print(f"[ERROR] Vendor '{vendor.vendor_name}' not configured properly.")
        return None

    full_url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    payload = build_vendor_request(vendor_key, request_data)

    headers = {"Content-Type": "application/json"}
    if vendor_key == "karza":
        headers["x-karza-key"] = vendor.uat_api_key
    elif vendor_key == "surepass":
        headers["Authorization"] = f"Bearer {SUREPASS_TOKEN}"

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


def normalize_vendor_response(vendor_name, raw_data):
    result = raw_data.get("result") or raw_data.get("data") or {}
    if not result:
        return None

    name = vendor_name.lower()

    if name == "karza":
        return {
            "client_id": raw_data.get("request_id"),
            "consumer_id": result.get("consumer_number") or result.get("consumer_id"),
            "customer_id": result.get("consumer_number") or result.get("consumer_id"),
            "full_name": result.get("consumer_name"),
            "address": result.get("address"),
            "mobile": result.get("mobile_number"),
            "email": result.get("email_address"),
            "bill_number": result.get("bill_no"),
            "bill_amount": sanitize_decimal(result.get("bill_amount") or result.get("amount_payable")),
            "bill_due_date": result.get("bill_due_date") or result.get("dueDate"),
            "bill_issue_date": result.get("bill_issue_date") or result.get("bill_date"),
            "bill_status": result.get("status"),
            "service_provider": result.get("service_provider"),
            "district": result.get("district"),
            "operator_code": result.get("operator_code"),
        }

    if name == "surepass":
        return {
            "client_id": result.get("client_id"),
            "consumer_id": result.get("customer_id") or result.get("id_number"),
            "customer_id": result.get("customer_id") or result.get("id_number"),
            "operator_code": result.get("operator_code"),
            "state": result.get("state"),
            "full_name": result.get("full_name"),
            "address": result.get("address"),
            "mobile": result.get("mobile"),
            "email": result.get("user_email"),
            "bill_number": result.get("bill_number"),
            "bill_amount": sanitize_decimal(result.get("bill_amount")),
            "bill_due_date": result.get("bill_due_date"),
            "bill_issue_date": result.get("bill_issue_date"),
            "bill_status": result.get("bill_status"),
            "document_link": result.get("document_link"),
        }

    return None


def sanitize_decimal(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    try:
        return Decimal(value)
    except Exception:
        return None


def save_bill_data(normalized, created_by):
    return UatElectricityBill.objects.create(
        client_id=normalized.get("client_id"),
        consumer_id=normalized.get("consumer_id"),
        customer_id=normalized.get("customer_id"),
        service_provider=normalized.get("service_provider"),
        operator_code=normalized.get("operator_code"),
        state=normalized.get("state"),
        district=normalized.get("district"),
        full_name=normalized.get("full_name"),
        address=normalized.get("address"),
        mobile=normalized.get("mobile"),
        reg_mobile_no=normalized.get("reg_mobile_no"),
        email=normalized.get("email"),
        bill_number=normalized.get("bill_number"),
        bill_amount=sanitize_decimal(normalized.get("bill_amount")),
        bill_due_date=normalized.get("bill_due_date"),
        bill_issue_date=normalized.get("bill_issue_date"),
        bill_status=normalized.get("bill_status"),
        document_link=normalized.get("document_link"),
        created_by=created_by,
    )


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
    payload = build_vendor_request(vendor_name, request_data)
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
