"""
Authentication endpoints for login, registration, and token management.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DuplicateResourceError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordChangeRequest,
    SignupRequest,
    SignupResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new tenant and admin user"
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new tenant with an admin user.
    
    Creates a new tenant organization and the first admin user for that tenant.
    The admin user can then invite other users to the tenant.
    """
    auth_service = AuthService(db)
    
    try:
        user, tenant = await auth_service.register_tenant(
            tenant_name=request.tenant_name,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        logger.info(
            "New tenant registered",
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            admin_email=user.email
        )
        
        return RegisterResponse(
            message="Registration successful",
            tenant_id=tenant.id,
            user_id=user.id,
            email=user.email
        )
    except DuplicateResourceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up to join an existing organization"
)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up as a new user to join an existing organization.
    
    Unlike /register (which creates a new org + admin), this endpoint
    allows users to join an existing organization as a regular USER.
    
    Requires a valid tenant_slug of an active organization.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.signup(request)
        
        logger.info(
            "User signed up",
            user_id=result.user_id,
            tenant_id=result.tenant_id,
            email=result.email
        )
        
        return result
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateResourceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and get access token"
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    Returns access token (short-lived) and refresh token (long-lived).
    Use refresh token to get new access tokens without re-authenticating.
    """
    auth_service = AuthService(db)
    
    try:
        user, access_token, refresh_token = await auth_service.authenticate(
            email=request.email,
            password=request.password
        )
        
        logger.info("User logged in", user_id=user.id, email=user.email)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                tenant_id=user.tenant_id,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login
            )
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get new access token using refresh token.
    
    Use this endpoint when your access token expires to get a new one
    without requiring the user to log in again.
    """
    auth_service = AuthService(db)
    
    try:
        access_token = await auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user's password"
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for the currently authenticated user.
    
    Requires the current password for verification before setting new password.
    """
    auth_service = AuthService(db)
    
    try:
        await auth_service.change_password(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        logger.info("Password changed", user_id=current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the profile of the currently authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login
    )
