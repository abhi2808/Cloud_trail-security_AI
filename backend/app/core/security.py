from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.core.config import settings

# Create bcrypt context inside security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, email: str) -> str:
    """Creates a JWT access token for a user."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    to_encode = {"exp": expire, "sub": str(user_id), "email": email}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodes and verifies a JWT token. Raises 401 if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials - token expired or invalid",
        )
