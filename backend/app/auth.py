"""
Authentication utilities for FastAPI application
JWT token generation and validation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.config import get_config


config = get_config()


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (e.g., {"student_id": "123"})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=config.auth.jwt_expiration_hours)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(
        to_encode,
        config.auth.jwt_secret_key,
        algorithm=config.auth.jwt_algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            config.auth.jwt_secret_key,
            algorithms=[config.auth.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def get_token_data(token: str) -> Optional[str]:
    """
    Extract student_id from token.

    Args:
        token: JWT token string

    Returns:
        Student ID or None if invalid
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("student_id")
    return None


# FastAPI dependency for protected routes
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency to get current student from JWT token.

    Usage in protected routes:
        @app.get("/protected-endpoint")
        def protected_route(student_id: str = Depends(get_current_student)):
            return {"message": f"Hello student {student_id}"}
    """
    token = credentials.credentials
    student_id = get_token_data(token)

    if student_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return student_id


async def get_current_student_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns student_id if token is valid, None otherwise.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    return get_token_data(token)
