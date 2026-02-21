"""
FastAPI dependencies for dependency injection.
Provides database sessions, authentication, and tenant context.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError, ResourceNotFoundError
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


# HTTP Bearer scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Automatically handles session lifecycle.
    """
    async for session in get_async_session():
        yield session


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = decode_access_token(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure current user is an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Alias for backward compatibility
get_current_tenant_admin = get_current_admin


async def verify_tenant_access(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Verify user has access to their tenant and tenant is active.
    
    Returns:
        tenant_id: The user's tenant ID
    """
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is suspended"
        )
    
    return current_user.tenant_id


class TenantContext:
    """
    Context class providing tenant-scoped data access.
    """
    
    def __init__(self, tenant_id: str, db: AsyncSession):
        self.tenant_id = tenant_id
        self.db = db


async def get_tenant_context(
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """
    Dependency to get tenant context for multi-tenant operations.
    """
    return TenantContext(tenant_id=tenant_id, db=db)


def require_role(*allowed_roles: UserRole):
    """
    Factory for creating role-based access dependencies.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    
    Args:
        allowed_roles: Roles that are allowed to access the endpoint
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user
    
    return role_checker


# Optional user dependency (for public endpoints that can be enhanced with auth)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None
    
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id:
            user_repo = UserRepository(db)
            return await user_repo.get_by_id(user_id)
    except Exception:
        pass
    
    return None
