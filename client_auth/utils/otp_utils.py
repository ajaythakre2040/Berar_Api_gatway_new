import random
import uuid
from datetime import timedelta
from django.utils import timezone
from client_auth.models.login_otp_verification import LoginOtpVerification
from client_auth.models.sms_log import SmsLog
from client_auth.utils.sms_utils import send_seized_emp_otp
from constant import DeliveryStatus, SmsType


def send_login_otp(client):
    otp_code = str(random.randint(100000, 999999))
    expiry_time = timezone.now() + timedelta(minutes=5)
    request_id = str(uuid.uuid4())

    LoginOtpVerification.objects.create(
        client=client,
        otp_code=otp_code,
        request_id=request_id,
        status=DeliveryStatus.PENDING,
        expires_at=expiry_time,
    )

    message = f"Your OTP for login is {otp_code}. It will expire in 5 minutes."

    sms_log = SmsLog.objects.create(
        user_id=str(client.id),
        mobile_number=client.phone,
        message=message,
        sms_type=SmsType.LOGIN_OTP,
        request_id=request_id,
        status=DeliveryStatus.PENDING,
    )

    sms_response = send_seized_emp_otp(client.phone, otp_code)

    if sms_response.get("error"):
        sms_log.status = DeliveryStatus.FAILED
    else:

        api_status = sms_response.get("status") or sms_response.get("success")
        if api_status in [True, "success", "SUCCESS"]:
            sms_log.status = DeliveryStatus.DELIVERED
        else:
            sms_log.status = DeliveryStatus.FAILED

    sms_log.response = str(sms_response)
    sms_log.save(update_fields=["status", "response"])

    return otp_code, expiry_time, request_id
