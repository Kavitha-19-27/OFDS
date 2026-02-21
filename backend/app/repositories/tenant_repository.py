"""
Tenant repository for tenant CRUD operations.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug.
        
        Args:
            slug: Tenant slug
            
        Returns:
            Tenant or None
        """
        query = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if slug already exists.
        
        Args:
            slug: Slug to check
            exclude_id: Optional ID to exclude from check (for updates)
            
        Returns:
            True if slug exists
        """
        query = select(Tenant.id).where(Tenant.slug == slug)
        
        if exclude_id:
            query = query.where(Tenant.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_active_tenants(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Tenant]:
        """
        Get all active tenants.
        
        Args:
            skip: Records to skip
            limit: Max records to return
            
        Returns:
            List of active tenants
        """
        query = (
            select(Tenant)
            .where(Tenant.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def deactivate(self, tenant_id: str) -> Optional[Tenant]:
        """
        Deactivate a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Updated tenant or None
        """
        tenant = await self.get_by_id(tenant_id)
        if tenant:
            tenant.is_active = False
            await self.session.flush()
            await self.session.refresh(tenant)
        return tenant
