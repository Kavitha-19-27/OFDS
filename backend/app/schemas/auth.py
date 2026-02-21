"""
Authentication schemas for login, token management.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, Field

if TYPE_CHECKING:
    from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")


class RefreshTokenResponse(BaseModel):
    """Response after refreshing access token."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str = Field(..., description="Subject (user ID)")
    tenant_id: str = Field(..., description="Tenant ID")
    role: str = Field(..., description="User role")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(default="access", description="Token type (access/refresh)")


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Registration request for new tenant with admin user."""
    # Tenant info - accept both tenant_name and organization_name
    tenant_name: str = Field(
        ...,
        min_length=2, 
        max_length=255,
        alias="organization_name"
    )
    tenant_slug: Optional[str] = Field(None, min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    
    # Admin user info
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)
    confirm_password: Optional[str] = Field(None, min_length=8)  # Accept but ignore
    
    model_config = {"populate_by_name": True}


class RegisterResponse(BaseModel):
    """Registration response."""
    tenant_id: str
    user_id: str
    email: str
    message: str = "Registration successful"


class SignupRequest(BaseModel):
    """Signup request for new users."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)


class SignupResponse(BaseModel):
    """Signup response."""
    user_id: str
    tenant_id: str
    email: str
    role: str
    message: str = "Signup successful"


class LoginResponse(BaseModel):
    """Login response with tokens and user info."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserResponse" = Field(..., description="User details")
    
    class Config:
        from_attributes = True


# Import at runtime to avoid circular imports
from app.schemas.user import UserResponse
LoginResponse.model_rebuild()
