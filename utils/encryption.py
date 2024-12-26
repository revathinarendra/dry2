from cryptography.fernet import Fernet
from django.conf import settings

# Initialize Fernet with the key from settings
fernet = Fernet(settings.ENCRYPTION_KEY)

def encrypt_id(id_value: int) -> str:
    """
    Encrypts an integer ID to a string.
    """
    id_bytes = str(id_value).encode()
    encrypted_id = fernet.encrypt(id_bytes)
    return encrypted_id.decode()

def decrypt_id(encrypted_id: str) -> int:
    """
    Decrypts an encrypted string ID back to an integer.
    """
    decrypted_bytes = fernet.decrypt(encrypted_id.encode())
    return int(decrypted_bytes.decode())
