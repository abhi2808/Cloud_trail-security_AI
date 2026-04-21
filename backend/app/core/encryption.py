import base64
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_fernet_instance() -> Fernet:
    """Helper to get a Fernet instance using the configured secret key."""
    return Fernet(settings.encryption_secret.encode('utf-8'))

def encrypt_value(plain_text: str) -> str:
    """
    Encrypts a plaintext string using Fernet symmetric encryption.
    Returns the encrypted string as a base64 encoded strong.
    """
    if not plain_text:
        return ""
    f = _get_fernet_instance()
    return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')

def decrypt_value(encrypted_text: str) -> str:
    """
    Decrypts a Fernet encrypted string back to plaintext.
    Raises ValueError if decryption fails.
    """
    if not encrypted_text:
        return ""
    f = _get_fernet_instance()
    try:
        return f.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
