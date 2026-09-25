"""
Security and Authentication Utilities
Password hashing (bcrypt) and JWT token generation/validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
try:
    import jwt
except ImportError:
    jwt = None  # type: ignore[assignment]
try:
    from app.config import settings
except Exception:
    settings = None  # type: ignore[assignment]
try:
    import bcrypt

    def hash_password(password: str) -> str:
        """Hash a plaintext password using direct bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against an existing bcrypt or fallback hash."""
        if not hashed_password:
            return False
        if hashed_password.startswith("sha256$"):
            import hashlib
            import hmac
            parts = hashed_password.split("$")
            if len(parts) != 3:
                return False
            salt, target_hash = parts[1], parts[2]
            test_hash = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
            return hmac.compare_digest(test_hash, target_hash)
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

except (ImportError, ModuleNotFoundError):
    import hashlib
    import hmac

    def hash_password(password: str) -> str:
        """Fallback SHA-256 password hashing if bcrypt is missing in test environment."""
        salt = "cogent_salt_"
        hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"sha256${salt}${hashed}"

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against fallback hash."""
        if not hashed_password.startswith("sha256$"):
            return False
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt, target_hash = parts[1], parts[2]
        test_hash = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(test_hash, target_hash)


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
