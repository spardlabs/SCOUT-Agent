import base64

from cryptography.fernet import Fernet

from scout.config import settings

# Derive a Fernet key from the app secret
_key = base64.urlsafe_b64encode(settings.app_secret_key.ljust(32)[:32].encode())
_fernet = Fernet(_key)


def encrypt_token(token: str) -> str:
    return _fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _fernet.decrypt(encrypted.encode()).decode()
