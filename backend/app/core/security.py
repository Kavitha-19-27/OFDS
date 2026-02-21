"""
Security utilities for JWT and password management.
Implements secure authentication patterns.
"""
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import AuthenticationError


# Password hashing context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor for bcrypt
    bcrypt__ident="2b"  # Use $2b$ format
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Bcrypt has a 72-byte limit, truncate if needed
    # Encode to bytes to handle unicode properly
    password_bytes = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Apply same truncation as hash_password for consistency
        password_bytes = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(password_bytes, hashed_password)
    except Exception:
        return False


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User ID (sub claim)
        tenant_id: Tenant ID for multi-tenancy
        role: User role for authorization
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    return jwt.encode(
        payload,
        settings.effective_jwt_secret,
        algorithm=settings.jwt_algorithm
    )


def create_refresh_token(
    subject: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: User ID (sub claim)
        tenant_id: Tenant ID
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    return jwt.encode(
        payload,
        settings.effective_jwt_secret,
        algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.effective_jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def validate_access_token(token: str) -> dict[str, Any]:
    """
    Validate an access token specifically.
    
    Args:
        token: JWT access token
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If not a valid access token
    """
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")
    
    return payload


def validate_refresh_token(token: str) -> dict[str, Any]:
    """
    Validate a refresh token specifically.
    
    Args:
        token: JWT refresh token
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If not a valid refresh token
    """
    payload = decode_token(token)
    
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")
    
    return payload


# Alias for backward compatibility
decode_access_token = validate_access_token
