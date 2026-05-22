import hashlib
import uuid
import secrets


def hash_string(data: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm."""
    h = hashlib.new(algorithm)
    h.update(data.encode("utf-8"))
    return h.hexdigest()


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    uid = str(uuid.uuid4())
    return f"{prefix}{uid}" if prefix else uid


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_hex(length)


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return secrets.compare_digest(a.encode(), b.encode())
