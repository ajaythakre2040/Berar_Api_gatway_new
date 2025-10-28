from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import Throttled



class ForgotPasswordThrottle(AnonRateThrottle):
    scope = "forgot_password"

    def throttle_failure(self):
        wait = self.wait() or 60
        minutes = int(wait // 60) or 1
        message = f"You've made too many password reset requests. Please try again in {minutes} minute(s)."
        raise Throttled(detail=message)


class ChangePasswordThrottle(UserRateThrottle):
    scope = "change_password"

    def throttle_failure(self):
        wait = self.wait() or 60  
        minutes = int(wait // 60) or 1  

        message = f"You have exceeded the allowed number of password change attempts. Please try again in {minutes} minute(s)."
        raise Throttled(detail=message)
