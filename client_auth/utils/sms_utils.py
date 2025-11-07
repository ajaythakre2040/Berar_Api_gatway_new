import requests
API_SMS_KEY = "a0ee6f-c9fb61-bff895-6094c1-b47ac5"
def send_seized_emp_otp(mobile_number, otp):
    url = "http://api.pinnacle.in/index.php/sms/json"
    headers = {
        "apikey": API_SMS_KEY,
        "Content-Type": "application/json",
        "Cookie": 'DO-LB="MTAuMTM5LjIyMy4xMTA6ODA="; PHPSESSID=1fo6rqls3mecq8ge6e7q6k2mmf',
    }
    payload = {
        "sender": "berarf",
        "message": [
            {
                "number": f"91{mobile_number}",
                "text": f"Dear User, Use this One Time Password: {otp} to verify your mobile number.\nIt is valid for the next 3 Minutes. Thank You Berar Finance Limited"
            }
        ],
        "messagetype": "TXT",
        "dlttempid": "1707170659123947276"
    }
    response = requests.post(url, json=payload, headers=headers)
    try:
        return response.json()
    except Exception as e:
        return {"error": "Invalid response", "content": response.text}
    
    

def send_link(mobile_number, link):
    url = "http://api.pinnacle.in/index.php/sms/json"
    headers = {
        "apikey": API_SMS_KEY,
        "Content-Type": "application/json",
        "Cookie": 'DO-LB="MTAuMTM5LjIyMy4xMTA6ODA="; PHPSESSID=1fo6rqls3mecq8ge6e7q6k2mmf',
    }
    payload = {
        "sender": "berarf",
        "message": [
            {
                "number": f"91{mobile_number}",
                "text": f"Dear User, This is your link {link}. Thank You Berar Finance Limited"
            }
        ],
        "messagetype": "TXT",
        "dlttempid": "1707170659123947276"
    }
    response = requests.post(url, json=payload, headers=headers)
    try:
        return response.json()
    except Exception as e:
        return {"error": "Invalid response", "content": response.text}