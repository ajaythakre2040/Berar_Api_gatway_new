import requests
from decouple import config
from kyc_api_gateway.models import UatVoterDetail
from kyc_api_gateway.utils.constants import VENDOR_VOTER_SERVICE_ENDPOINTS, DEFAULT_COUNTRY

SUREPASS_TOKEN = config("SUREPASS_TOKEN", default=None)
if not SUREPASS_TOKEN:
    raise ValueError("SUREPASS_TOKEN is not set in your environment variables.")


def build_vendor_request(vendor_name, request_data):
    vendor_key = vendor_name.lower()
    if vendor_key == "karza":
        return {
            "consent": request_data.get("consent", "Y"),
            "epicNo": request_data.get("id_number"),
            "clientData": {"caseId": request_data.get("case_id", "123456")},
        }
    elif vendor_key == "surepass":
        return {
            "id_number": request_data.get("id_number")
        }
    return request_data


def call_voter_vendor_api(vendor, request_data):
    vendor_key = vendor.vendor_name.lower()
    endpoint_path = VENDOR_VOTER_SERVICE_ENDPOINTS.get(vendor_key)
    base_url = vendor.uat_base_url


    if not endpoint_path or not base_url:
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
    if not raw_data:
        return None

    vendor_key = vendor_name.lower()
    result = raw_data.get("result") or raw_data.get("data") or {}

    if vendor_key == "karza":
        if raw_data.get("statusCode") != 101 or not result:
            return None

        return {
            "vendor": vendor_key,
            "client_id": raw_data.get("clientData", {}).get("caseId"),
            "epic_no": result.get("epicNo"),
            "input_voter_id": result.get("epicNo"),
            "name": result.get("name"),
            "relation_name": result.get("rlnName"),
            "relation_type": result.get("rlnType"),
            "gender": result.get("gender"),
            "dob": result.get("dob"),
            "age": str(result.get("age", "")),
            "district": result.get("district"),
            "state": result.get("state"),
            "assembly_constituency": result.get("acName"),
            "assembly_constituency_number": result.get("acNo"),
            "polling_station": result.get("psName"),
            "part_no": result.get("partNo"),
            "part_name": result.get("partName"),
            "slno_in_part": result.get("slNoInPart"),
            "ps_lat_long": result.get("psLatLong"),
            "name_v1": result.get("nameV1"),
            "name_v2": result.get("nameV2"),
            "name_v3": result.get("nameV3"),
            "rln_name_v1": result.get("rlnNameV1"),
            "rln_name_v2": result.get("rlnNameV2"),
            "rln_name_v3": result.get("rlnNameV3"),
            "house_no": result.get("houseNo"),
            "last_update": result.get("lastUpdate"),
            "st_code": result.get("stCode"),
            "parliamentary_name": result.get("pcName"),
            "parliamentary_number": result.get("acNo"),
        }

    if vendor_key == "surepass":
        if not raw_data.get("success") or not result:
            return None

        return {
            "vendor": vendor_key,
            "client_id": result.get("client_id"),
            "epic_no": result.get("epic_no"),
            "input_voter_id": result.get("epic_no"),
            "name": result.get("name"),
            "relation_name": result.get("name_v1"),
            "relation_type": None,  
            "gender": "male" if str(result.get("gender", "")).lower().startswith("m") else "female",
            "dob": result.get("dob"),
            "age": str(result.get("age", "")),
            "district": result.get("district"),
            "state": result.get("state"),
            "assembly_constituency": result.get("assembly_constituency"),
            "assembly_constituency_number": result.get("assembly_constituency_number"),
            "polling_station": result.get("polling_station"),
            "part_no": result.get("part_number"),
            "part_name": result.get("part_name"),
            "slno_in_part": result.get("slno_in_part"),
            "ps_lat_long": result.get("ps_lat_long"),
            "name_v1": result.get("name_v1"),
            "name_v2": result.get("name_v2"),
            "name_v3": result.get("name_v3"),
            "rln_name_v1": result.get("rln_name_v1"),
            "rln_name_v2": result.get("rln_name_v2"),
            "rln_name_v3": result.get("rln_name_v3"),
            "house_no": result.get("house_no"),
            "last_update": result.get("last_update"),
            "st_code": result.get("st_code"),
            "parliamentary_name": result.get("parliamentary_name"),
            "parliamentary_number": result.get("parliamentary_number"),
        }

    return None


def save_voter_data(normalized, created_by):
    if not normalized:
        return None

    try:
        voter_obj = UatVoterDetail.objects.create(
            vendor=normalized.get("vendor"),
            client_id=normalized.get("client_id"),
            epic_no=normalized.get("epic_no"),
            input_voter_id=normalized.get("input_voter_id"),
            name=normalized.get("name"),
            relation_name=normalized.get("relation_name"),
            relation_type=normalized.get("relation_type"),
            gender=normalized.get("gender"),
            dob=normalized.get("dob"),
            age=normalized.get("age"),
            district=normalized.get("district"),
            state=normalized.get("state"),
            assembly_constituency=normalized.get("assembly_constituency"),
            assembly_constituency_number=normalized.get("assembly_constituency_number"),
            polling_station=normalized.get("polling_station"),
            part_no=normalized.get("part_no"),
            part_name=normalized.get("part_name"),
            slno_in_part=normalized.get("slno_in_part"),
            ps_lat_long=normalized.get("ps_lat_long"),
            name_v1=normalized.get("name_v1"),
            name_v2=normalized.get("name_v2"),
            name_v3=normalized.get("name_v3"),
            rln_name_v1=normalized.get("rln_name_v1"),
            rln_name_v2=normalized.get("rln_name_v2"),
            rln_name_v3=normalized.get("rln_name_v3"),
            house_no=normalized.get("house_no"),
            last_update=normalized.get("last_update"),
            st_code=normalized.get("st_code"),
            parliamentary_name=normalized.get("parliamentary_name"),
            parliamentary_number=normalized.get("parliamentary_number"),
            voter_id=normalized.get("epic_no"),  
            created_by=created_by
        )
        return voter_obj
    except Exception as e:
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
