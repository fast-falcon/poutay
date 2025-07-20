from cryptography.fernet import Fernet
import base64
import hashlib

def get_fernet_key(password: str) -> Fernet:
    hashed = hashlib.sha256(password.encode()).digest()
    key = base64.urlsafe_b64encode(hashed)
    return Fernet(key)
