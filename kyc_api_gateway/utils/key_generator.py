import secrets
import string

def generate_secure_token(length=20):

    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


