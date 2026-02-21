"""
Tenant service for tenant management operations.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.models.tenant import Tenant
from app.repositories.tenant_repository import TenantRepository
from app.repositories.document_repository import DocumentRepository, DocumentChunkRepository
from app.repositories.chat_repository import ChatRepository
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantStatsResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TenantService:
    """Service for tenant management operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_repo = TenantRepository(session)
        self.document_repo = DocumentRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)
        self.chat_repo = ChatRepository(session)
    
    async def create_tenant(self, data: TenantCreate) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            data: Tenant creation data
            
        Returns:
            Created tenant
            
        Raises:
            ConflictError: If slug already exists
        """
        # Check slug uniqueness
        if await self.tenant_repo.slug_exists(data.slug):
            raise ConflictError(f"Tenant with slug '{data.slug}' already exists")
        
        tenant = await self.tenant_repo.create(
            name=data.name,
            slug=data.slug,
            max_documents=data.max_documents,
            max_storage_mb=data.max_storage_mb,
            is_active=True
        )
        
        logger.info("Tenant created", tenant_id=tenant.id, slug=tenant.slug)
        return tenant
    
    async def get_tenant(self, tenant_id: str) -> Tenant:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant instance
            
        Raises:
            NotFoundError: If tenant not found
        """
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(
                "Tenant not found",
                resource_type="tenant",
                resource_id=tenant_id
            )
        return tenant
    
    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        """
        Get tenant by slug.
        
        Args:
            slug: Tenant slug
            
        Returns:
            Tenant instance
            
        Raises:
            NotFoundError: If tenant not found
        """
        tenant = await self.tenant_repo.get_by_slug(slug)
        if not tenant:
            raise NotFoundError(
                f"Tenant with slug '{slug}' not found",
                resource_type="tenant"
            )
        return tenant
    
    async def update_tenant(
        self,
        tenant_id: str,
        data: TenantUpdate
    ) -> Tenant:
        """
        Update tenant details.
        
        Args:
            tenant_id: Tenant ID
            data: Update data
            
        Returns:
            Updated tenant
            
        Raises:
            NotFoundError: If tenant not found
        """
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError(
                "Tenant not found",
                resource_type="tenant",
                resource_id=tenant_id
            )
        
        update_data = data.model_dump(exclude_unset=True)
        tenant = await self.tenant_repo.update(tenant, **update_data)
        
        logger.info("Tenant updated", tenant_id=tenant_id, fields=list(update_data.keys()))
        return tenant
    
    async def deactivate_tenant(self, tenant_id: str) -> Tenant:
        """
        Deactivate a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Deactivated tenant
            
        Raises:
            NotFoundError: If tenant not found
        """
        tenant = await self.tenant_repo.deactivate(tenant_id)
        if not tenant:
            raise NotFoundError(
                "Tenant not found",
                resource_type="tenant",
                resource_id=tenant_id
            )
        
        logger.info("Tenant deactivated", tenant_id=tenant_id)
        return tenant
    
    async def get_tenant_stats(self, tenant_id: str) -> TenantStatsResponse:
        """
        Get tenant usage statistics.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            TenantStatsResponse with usage data
        """
        tenant = await self.get_tenant(tenant_id)
        
        # Get document count
        total_documents = await self.document_repo.count_by_tenant(tenant_id)
        
        # Get chunk count
        total_chunks = await self.chunk_repo.count_by_tenant(tenant_id)
        
        # Get total queries
        total_queries = await self.chat_repo.count_by_tenant(tenant_id)
        
        # Get storage used
        storage_bytes = await self.document_repo.get_total_storage(tenant_id)
        storage_mb = round(storage_bytes / (1024 * 1024), 2)
        
        return TenantStatsResponse(
            tenant_id=tenant_id,
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_queries=total_queries,
            storage_used_mb=storage_mb,
            storage_limit_mb=tenant.max_storage_mb,
            document_limit=tenant.max_documents
        )
    
    async def check_document_limit(self, tenant_id: str) -> tuple[bool, int, int]:
        """
        Check if tenant can upload more documents.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (can_upload, current_count, max_count)
        """
        tenant = await self.get_tenant(tenant_id)
        current_count = await self.document_repo.count_by_tenant(tenant_id)
        return (
            current_count < tenant.max_documents,
            current_count,
            tenant.max_documents
        )
    
    async def check_storage_limit(
        self,
        tenant_id: str,
        additional_bytes: int
    ) -> tuple[bool, float, float]:
        """
        Check if tenant has enough storage.
        
        Args:
            tenant_id: Tenant ID
            additional_bytes: Bytes to be added
            
        Returns:
            Tuple of (has_space, current_mb, max_mb)
        """
        tenant = await self.get_tenant(tenant_id)
        current_bytes = await self.document_repo.get_total_storage(tenant_id)
        current_mb = current_bytes / (1024 * 1024)
        max_mb = tenant.max_storage_mb
        
        new_total_mb = (current_bytes + additional_bytes) / (1024 * 1024)
        
        return (new_total_mb <= max_mb, round(current_mb, 2), max_mb)
