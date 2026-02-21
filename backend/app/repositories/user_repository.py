"""
User repository for user CRUD operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(
        self,
        email: str,
        tenant_id: str
    ) -> Optional[User]:
        """
        Get user by email within a tenant.
        
        Args:
            email: User email
            tenant_id: Tenant ID
            
        Returns:
            User or None
        """
        query = select(User).where(
            and_(
                User.email == email,
                User.tenant_id == tenant_id
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email_global(self, email: str) -> Optional[User]:
        """
        Get user by email globally (across all tenants).
        
        Args:
            email: User email
            
        Returns:
            User or None
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def email_exists(
        self,
        email: str,
        tenant_id: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """
        Check if email exists within a tenant.
        
        Args:
            email: Email to check
            tenant_id: Tenant ID
            exclude_id: Optional user ID to exclude
            
        Returns:
            True if email exists
        """
        query = select(User.id).where(
            and_(
                User.email == email,
                User.tenant_id == tenant_id
            )
        )
        
        if exclude_id:
            query = query.where(User.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_by_tenant(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[User]:
        """
        Get all users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            skip: Records to skip
            limit: Max records to return
            active_only: Only return active users
            
        Returns:
            List of users
        """
        query = select(User).where(User.tenant_id == tenant_id)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_admins(self, tenant_id: str) -> List[User]:
        """
        Get all admin users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of admin users
        """
        query = select(User).where(
            and_(
                User.tenant_id == tenant_id,
                User.role == UserRole.ADMIN,
                User.is_active == True
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_last_login(self, user_id: str) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user or None
        """
        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(user)
        return user
    
    async def deactivate(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[User]:
        """
        Deactivate a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            Updated user or None
        """
        user = await self.get_by_id(user_id, tenant_id)
        if user:
            user.is_active = False
            await self.session.flush()
            await self.session.refresh(user)
        return user
    
    async def change_role(
        self,
        user_id: str,
        tenant_id: str,
        new_role: UserRole
    ) -> Optional[User]:
        """
        Change user's role.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            new_role: New role
            
        Returns:
            Updated user or None
        """
        user = await self.get_by_id(user_id, tenant_id)
        if user:
            user.role = new_role
            await self.session.flush()
            await self.session.refresh(user)
        return user
