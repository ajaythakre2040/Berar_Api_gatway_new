import difflib
import uuid
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from kyc_api_gateway.models import UatAddressMatchRequestLog

class CustomAddressMatchAPIView(APIView):

    def post(self, request):
        try:
            address1 = request.data.get("address1", "").strip()
            address2 = request.data.get("address2", "").strip()
            client_id = str(request.data.get("client_id", uuid.uuid4()))

            if not address1 or not address2:
                return Response(
                    {"error": "Both address1 and address2 are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ratio = difflib.SequenceMatcher(None, address1.lower(), address2.lower()).ratio()
            score = round(ratio, 2)
            is_match = score >= 0.80  # threshold 80%

            address_state = self._extract_state(address1, address2)
            address_district = self._extract_district(address1, address2)
            address_locality = self._extract_locality(address1, address2)
            address_pincode = self._extract_pincode(address1, address2)

            request_id = str(uuid.uuid4())

            response_data = {
                "id": None,
                "match": is_match,
                "score": score,
                "success": True,
                "message": "Address matched successfully" if is_match else "Address not matched",
                "status_code": 101,
                "client_id": client_id,
                "request_id": request_id,
                "district": address_district,
                "state": address_state,
                "locality": address_locality,
                "pincode": address_pincode,
                "address_state": address_state,
                "address_district": address_district,
                "address_locality": address_locality,
                "address_pincode": address_pincode,
                "created_at": timezone.now(),
            }

            UatAddressMatchRequestLog.objects.create(
                client_id=client_id,
                request_payload=request.data,
                response_payload=response_data,
                created_at=timezone.now()
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _extract_pincode(self, *addresses):
        import re
        for addr in addresses:
            match = re.search(r"\b\d{6}\b", addr)
            if match:
                return int(match.group())
        return None

    def _extract_state(self, *addresses):
        states = ["MAHARASHTRA", "DELHI", "GUJARAT", "KARNATAKA", "TAMIL NADU"]
        for addr in addresses:
            for st in states:
                if st.lower() in addr.lower():
                    return st
        return None

    def _extract_district(self, *addresses):
        known = ["NAGPUR", "PUNE", "MUMBAI", "BENGALURU", "CHENNAI"]
        for addr in addresses:
            for dist in known:
                if dist.lower() in addr.lower():
                    return dist
        return None

    def _extract_locality(self, *addresses):
        # Just return first two words if available
        for addr in addresses:
            parts = addr.split()
            if len(parts) > 2:
                return " ".join(parts[:3])
        return None
