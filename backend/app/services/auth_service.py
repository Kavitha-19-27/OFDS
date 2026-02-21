"""
Authentication service for login, registration, and token management.
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.schemas.auth import (
    TokenResponse,
    RegisterRequest,
    RegisterResponse,
    SignupRequest,
    SignupResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)
    
    async def login(
        self,
        email: str,
        password: str,
        tenant_slug: str
    ) -> Tuple[TokenResponse, User]:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User email
            password: User password
            tenant_slug: Tenant slug
            
        Returns:
            Tuple of (TokenResponse, User)
            
        Raises:
            AuthenticationError: If credentials are invalid
            NotFoundError: If tenant not found
        """
        # Find tenant
        tenant = await self.tenant_repo.get_by_slug(tenant_slug)
        if not tenant:
            logger.warning("Login attempt for unknown tenant", tenant_slug=tenant_slug)
            raise NotFoundError("Tenant not found", resource_type="tenant")
        
        if not tenant.is_active:
            raise AuthenticationError("Tenant is inactive")
        
        # Find user
        user = await self.user_repo.get_by_email(email, tenant.id)
        if not user:
            logger.warning(
                "Login attempt for unknown user",
                email=email,
                tenant_id=tenant.id
            )
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(
                "Failed login attempt",
                user_id=user.id,
                email=email
            )
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        # Update last login
        await self.user_repo.update_last_login(user.id)
        
        # Generate tokens
        access_token = create_access_token(
            subject=user.id,
            tenant_id=tenant.id,
            role=user.role.value
        )
        
        refresh_token = create_refresh_token(
            subject=user.id,
            tenant_id=tenant.id
        )
        
        logger.info("User logged in", user_id=user.id, tenant_id=tenant.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        ), user
    
    async def authenticate(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user by email (global lookup) and return tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (User, access_token, refresh_token)
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email globally
        user = await self.user_repo.get_by_email_global(email)
        if not user:
            logger.warning("Login attempt for unknown user", email=email)
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt", user_id=user.id, email=email)
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        # Get tenant and verify it's active
        tenant = await self.tenant_repo.get_by_id(user.tenant_id)
        if not tenant or not tenant.is_active:
            raise AuthenticationError("Tenant is inactive")
        
        # Update last login
        await self.user_repo.update_last_login(user.id)
        
        # Generate tokens
        access_token = create_access_token(
            subject=user.id,
            tenant_id=tenant.id,
            role=user.role.value
        )
        
        refresh_token = create_refresh_token(
            subject=user.id,
            tenant_id=tenant.id
        )
        
        logger.info("User authenticated", user_id=user.id, tenant_id=tenant.id)
        
        return user, access_token, refresh_token
    
    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New TokenResponse
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Validate refresh token
        payload = validate_refresh_token(refresh_token)
        
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        # Verify user still exists and is active
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Verify tenant is still active
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant or not tenant.is_active:
            raise AuthenticationError("Tenant not found or inactive")
        
        # Generate new tokens
        new_access_token = create_access_token(
            subject=user.id,
            tenant_id=tenant.id,
            role=user.role.value
        )
        
        new_refresh_token = create_refresh_token(
            subject=user.id,
            tenant_id=tenant.id
        )
        
        logger.info("Tokens refreshed", user_id=user.id)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def register_tenant(
        self,
        tenant_name: str,
        email: str,
        password: str,
        full_name: str = None
    ) -> Tuple[User, Tenant]:
        """
        Register a new tenant with admin user.
        
        Args:
            tenant_name: Name of the tenant organization
            email: Admin user email
            password: Admin user password
            full_name: Admin user full name
            
        Returns:
            Tuple of (User, Tenant)
            
        Raises:
            ConflictError: If email already exists
        """
        import re
        
        # Generate slug from tenant name
        slug = re.sub(r'[^a-z0-9]+', '-', tenant_name.lower()).strip('-')
        
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email_global(email)
        if existing_user:
            raise ConflictError(f"Email '{email}' is already registered")
        
        # Check if slug exists and make unique if needed
        base_slug = slug
        counter = 1
        while await self.tenant_repo.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create tenant
        tenant = await self.tenant_repo.create(
            name=tenant_name,
            slug=slug,
            is_active=True
        )
        
        # Create admin user
        hashed_pwd = hash_password(password)
        user = await self.user_repo.create(
            tenant_id=tenant.id,
            email=email,
            hashed_password=hashed_pwd,
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        await self.session.commit()
        
        logger.info(
            "New tenant registered",
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            admin_email=user.email
        )
        
        return user, tenant
    
    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """
        Register a new tenant with admin user.
        
        Args:
            request: Registration request data
            
        Returns:
            RegisterResponse with tenant and user IDs
            
        Raises:
            ConflictError: If tenant slug already exists
        """
        # Check if tenant slug exists
        if await self.tenant_repo.slug_exists(request.tenant_slug):
            raise ConflictError(
                f"Tenant with slug '{request.tenant_slug}' already exists"
            )
        
        # Create tenant
        tenant = await self.tenant_repo.create(
            name=request.tenant_name,
            slug=request.tenant_slug,
            is_active=True
        )
        
        # Create admin user
        hashed_pwd = hash_password(request.password)
        user = await self.user_repo.create(
            tenant_id=tenant.id,
            email=request.email,
            hashed_password=hashed_pwd,
            full_name=request.full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        logger.info(
            "New tenant registered",
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            admin_email=user.email
        )
        
        return RegisterResponse(
            tenant_id=tenant.id,
            user_id=user.id,
            email=user.email
        )
    
    async def change_password(
        self,
        user_id: str,
        tenant_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user's password.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password changed
            
        Raises:
            AuthenticationError: If current password is wrong
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError("User not found", resource_type="user")
        
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        user.hashed_password = hash_password(new_password)
        await self.session.flush()
        
        logger.info("Password changed", user_id=user_id)
        return True

    async def signup(self, request: SignupRequest) -> SignupResponse:
        """
        Sign up a new user as USER role.
        
        Args:
            request: Signup request data
            
        Returns:
            SignupResponse with user details
            
        Raises:
            ConflictError: If email already exists
        """
        # Use Platform tenant for all users
        tenant = await self.tenant_repo.get_by_slug("platform")
        if not tenant:
            raise NotFoundError("Platform not configured. Contact administrator.")
        
        # Check if email exists
        if await self.user_repo.email_exists(request.email, tenant.id):
            raise ConflictError(f"User with email '{request.email}' already exists")
        
        # Create user with USER role
        hashed_pwd = hash_password(request.password)
        user = await self.user_repo.create(
            tenant_id=tenant.id,
            email=request.email,
            hashed_password=hashed_pwd,
            full_name=request.full_name or request.email.split('@')[0],
            role=UserRole.USER,  # Always USER for signup
            is_active=True
        )
        
        await self.session.commit()
        
        logger.info(
            "User signed up",
            user_id=user.id,
            email=user.email,
            role="USER"
        )
        
        return SignupResponse(
            user_id=user.id,
            tenant_id=tenant.id,
            email=user.email,
            role="USER"
        )
