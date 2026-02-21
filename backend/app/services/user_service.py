"""
User service for user management operations.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    AuthorizationError,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
    
    async def create_user(
        self,
        tenant_id: str,
        data: UserCreate,
        created_by_role: UserRole
    ) -> User:
        """
        Create a new user within a tenant.
        
        Args:
            tenant_id: Tenant ID
            data: User creation data
            created_by_role: Role of the user creating this user
            
        Returns:
            Created user
            
        Raises:
            ConflictError: If email already exists
            AuthorizationError: If trying to create higher-role user
        """
        # Check if email already exists in tenant
        if await self.user_repo.email_exists(data.email, tenant_id):
            raise ConflictError(f"User with email '{data.email}' already exists")
        
        # Prevent privilege escalation - only admin can create admin
        if data.role == UserRole.ADMIN and created_by_role != UserRole.ADMIN:
            raise AuthorizationError("Only admin can create admin users")
        
        # Create user
        user = await self.user_repo.create(
            tenant_id=tenant_id,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True
        )
        
        logger.info(
            "User created",
            user_id=user.id,
            email=user.email,
            tenant_id=tenant_id
        )
        
        return user
    
    async def get_user(
        self,
        user_id: str,
        tenant_id: str
    ) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            User instance
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError("User not found", resource_type="user", resource_id=user_id)
        return user
    
    async def get_users(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = True
    ) -> UserListResponse:
        """
        Get paginated list of users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            page: Page number (1-indexed)
            page_size: Number of users per page
            active_only: Only return active users
            
        Returns:
            UserListResponse with users and pagination info
        """
        skip = (page - 1) * page_size
        
        users = await self.user_repo.get_by_tenant(
            tenant_id=tenant_id,
            skip=skip,
            limit=page_size,
            active_only=active_only
        )
        
        total = await self.user_repo.count(tenant_id)
        pages = (total + page_size - 1) // page_size
        
        return UserListResponse(
            users=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    
    async def update_user(
        self,
        user_id: str,
        tenant_id: str,
        data: UserUpdate,
        updated_by_role: UserRole
    ) -> User:
        """
        Update user details.
        
        Args:
            user_id: User ID to update
            tenant_id: Tenant ID
            data: Update data
            updated_by_role: Role of the user performing the update
            
        Returns:
            Updated user
            
        Raises:
            NotFoundError: If user not found
            ConflictError: If email already taken
            AuthorizationError: If privilege escalation attempted
        """
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError("User not found", resource_type="user", resource_id=user_id)
        
        # Check email uniqueness if being changed
        if data.email and data.email != user.email:
            if await self.user_repo.email_exists(data.email, tenant_id, exclude_id=user_id):
                raise ConflictError(f"Email '{data.email}' is already taken")
        
        # Prevent privilege escalation for role changes
        if data.role:
            if data.role == UserRole.ADMIN and updated_by_role != UserRole.ADMIN:
                raise AuthorizationError("Only admin can assign admin role")
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user, **update_data)
        
        logger.info("User updated", user_id=user_id, fields=list(update_data.keys()))
        return user
    
    async def delete_user(
        self,
        user_id: str,
        tenant_id: str,
        deleted_by_id: str
    ) -> bool:
        """
        Soft delete (deactivate) a user.
        
        Args:
            user_id: User ID to delete
            tenant_id: Tenant ID
            deleted_by_id: ID of user performing deletion
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If user not found
            AuthorizationError: If trying to delete self
        """
        if user_id == deleted_by_id:
            raise AuthorizationError("Cannot delete your own account")
        
        user = await self.user_repo.deactivate(user_id, tenant_id)
        if not user:
            raise NotFoundError("User not found", resource_type="user", resource_id=user_id)
        
        logger.info("User deactivated", user_id=user_id, by=deleted_by_id)
        return True

    async def deactivate_user(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            Deactivated user or None if not found
        """
        user = await self.user_repo.deactivate(user_id, tenant_id)
        if user:
            logger.info("User deactivated", user_id=user_id)
        return user

    async def activate_user(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            Activated user or None if not found
        """
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if user:
            user.is_active = True
            await self.session.flush()
            await self.session.refresh(user)
            logger.info("User activated", user_id=user_id)
        return user
    
    async def get_admins(self, tenant_id: str) -> List[User]:
        """
        Get all admin users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of admin users
        """
        return await self.user_repo.get_admins(tenant_id)
