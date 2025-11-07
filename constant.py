ADMIN_USER = {
    "first_name": "Admin",
    "last_name": "User",
    "email": "admin@gmail.com",
    "mobile_number": "1234567890",
    "username": "admin",
    "password": "Admin@123",
    "position": "System Admin",
    "role_id": 1,  # Role will be created and assigned if missing
    "department_id": 1,  # Optional, safe to skip
}
# Status codes as integers
STATUS_ACTIVE = 1
STATUS_INACTIVE = 2
STATUS_SUSPENDED = 3
STATUS_PENDING = 4
STATUS_LOCKED = 5

# Optional mapping for labels (sirf display ke liye)
USER_STATUS = {
    1: "Active",
    2: "Inactive",
    3: "Suspended",
    4: "Pending",
    5: "Locked",
}
USER_STATUS_CHOICES = [(k, v) for k, v in USER_STATUS.items()]
MAX_LOGIN_ATTEMPTS = 5

KYC_MY_SERVICES = {
    "PAN": 1,
    "BILL": 2,
    "VOTER": 3,
    "NAME": 4,
    "RC": 5,
    "DRIVING": 6,
    "PASSPORT": 8,
    "ADDRESS": 9,
}
