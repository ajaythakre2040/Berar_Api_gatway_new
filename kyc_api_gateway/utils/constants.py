VENDOR_SERVICE_ENDPOINTS = {
    "karza": "v3/pan-profile",
    "surepass": "api/v1/pan/pan-comprehensive",
}

VENDOR_BILL_SERVICE_ENDPOINTS = {
    "karza": "v2/elec",
    "surepass": "api/v1/utility/electricity/",
}

VENDOR_NAME_SERVICE_ENDPOINTS = {
    "karza": "v3/name",
    "surepass": "api/v1/utils/name-matching/",
}

VENDOR_VOTER_SERVICE_ENDPOINTS = {
    "karza": "v3/voter",
    "surepass": "api/v1/voter-id/voter-id",
}

VENDOR_RC_SERVICE_ENDPOINTS = {
    "karza": "v3/rc-advanced",
    "surepass": "/api/v1/rc/rc-full",
}

VENDOR_DRIVING_LICENSE_ENDPOINTS = {
    "karza": "v3/dl",
    "surepass": "api/v1/driving-license/driving-license",
}


VENDOR_PASSPORT_SERVICE_ENDPOINTS = {
    "karza": "v3/passport-verification",
    "surepass": "api/v1/passport/passport/passport-details",
}

VENDOR_ADDRESS_SERVICE_ENDPOINTS = {
    "karza": "v3/address",
    "internal": "custom-address-match/",
}

DEFAULT_COUNTRY = "India"