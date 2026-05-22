import os
import base64
import hashlib
from typing import Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryption:
    """Data encryption at rest using AES-256."""
    
    def __init__(self, key: bytes = None):
        if key:
            self._key = key
            self._fernet = Fernet(key)
        else:
            self._key = None
            self._fernet = None
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """Derive a key from a password."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def set_key(self, key: bytes) -> None:
        """Set the encryption key."""
        self._key = key
        self._fernet = Fernet(key)
    
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data."""
        if self._fernet is None:
            raise ValueError("No encryption key set")
        
        if isinstance(data, str):
            data = data.encode()
        
        return self._fernet.encrypt(data)
    
    def decrypt(self, encrypted: bytes) -> bytes:
        """Decrypt data."""
        if self._fernet is None:
            raise ValueError("No encryption key set")
        
        return self._fernet.decrypt(encrypted)
    
    def decrypt_string(self, encrypted: bytes) -> str:
        """Decrypt data and return as string."""
        return self.decrypt(encrypted).decode()
    
    def rotate_key(self, new_key: bytes, encrypted_data: list[bytes]) -> list[bytes]:
        """Rotate encryption key and re-encrypt data."""
        if self._fernet is None:
            raise ValueError("No encryption key set")
        
        decrypted = [self.decrypt(d) for d in encrypted_data]
        
        self.set_key(new_key)
        
        return [self.encrypt(d) for d in decrypted]
    
    @staticmethod
    def hash_data(data: Union[str, bytes]) -> str:
        """Create SHA-256 hash of data."""
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha256(data).hexdigest()
