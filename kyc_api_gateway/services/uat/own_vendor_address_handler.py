import uuid
from fuzzywuzzy import fuzz
from decimal import Decimal



def internal_vendor_match(address1, address2):
    address1 = address1.strip().lower() if address1 else ""
    address2 = address2.strip().lower() if address2 else ""

    words1 = address1.split()
    words2 = address2.split()

    match_scores = []

    for w1 in words1:
        word_scores = [fuzz.ratio(w1, w2) for w2 in words2]
        best_score = max(word_scores)
        match_scores.append(best_score)

    if not match_scores:
        match_score = 0
    else:
        match_score = sum(match_scores) / len(match_scores)

    if match_score >= 65:
        match_status = "MATCHED"  # Any score above 65 is considered a match
    else:
        match_status = "NOT MATCHED"

    return {
        "address1": address1,
        "address2": address2,
        "match_score": round(match_score, 2),
        "match_status": match_status,
    }


def normalize_internal_vendor_response(raw_data, request_data=None):
    client_id = raw_data.get("client_id", str(uuid.uuid4()))
    match_status = raw_data.get("match_status")
    if match_status == "MATCHED":
        match_status = True
    elif match_status == "NOT MATCHED":
        match_status = False
    else:
        match_status = None

    normalized_response = {
        "client_id": client_id,
        "request_id": None,
        "address1": raw_data.get("address1"),
        "address2": raw_data.get("address2"),
        "match_score": sanitize_decimal(raw_data.get("match_score")),
        "match_status": match_status,
    }

    return normalized_response


def sanitize_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None
