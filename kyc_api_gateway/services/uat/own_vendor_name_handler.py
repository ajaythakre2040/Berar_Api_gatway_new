import uuid
from fuzzywuzzy import fuzz
from decimal import Decimal

def internal_vendor_match(name1, name2):
   

    words1 = name1.lower().split()
    words2 = name2.lower().split()

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
        "name_1": name1,
        "name_2": name2,
        "match_score": round(match_score, 2),
        "match_status": match_status,
    }


def normalize_internal_vendor_response(raw_data, request_data=None):
    """
    Normalize the raw fuzzy match response for internal use.
    Converts match status to boolean and sanitizes the match score to Decimal format.
    """
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
        "name_1": raw_data.get("name_1"),
        "name_2": raw_data.get("name_2"),
        "match_score": sanitize_decimal(raw_data.get("match_score")),
        "match_status": match_status,
    }

    print("Normalized data for internal:", normalized_response)
    return normalized_response


def sanitize_decimal(value):
    """
    Sanitize the match score value to Decimal format for precision.
    Returns None if the value cannot be converted to Decimal.
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None
