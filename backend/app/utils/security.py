"""
app/utils/security.py

Manages password hashing and JWT token generation/validation.
"""
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from app.config import settings

import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the hashed version using bcrypt."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a JSON Web Token (JWT) for authentication.
    
    Args:
        data: The payload to encode (usually the username/email).
        expires_delta: Optional custom expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration timestamp to the payload
    to_encode.update({"exp": expire})
    
    # Generate the JWT using the secret key and defined algorithm
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
