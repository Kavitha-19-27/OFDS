"""
Tenant schemas for multi-tenancy management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str = Field(..., min_length=2, max_length=255, description="Tenant name")
    slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="URL-friendly slug"
    )


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    max_documents: int = Field(default=100, ge=1, le=10000)
    max_storage_mb: int = Field(default=500, ge=10, le=10000)


class TenantUpdate(BaseModel):
    """Schema for updating tenant details."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
    max_documents: Optional[int] = Field(None, ge=1, le=10000)
    max_storage_mb: Optional[int] = Field(None, ge=10, le=10000)


class TenantResponse(BaseModel):
    """Tenant response schema."""
    id: str
    name: str
    slug: str
    is_active: bool
    max_documents: int
    max_storage_mb: int
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    user_count: Optional[int] = None
    document_count: Optional[int] = None
    storage_used_mb: Optional[float] = None
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Paginated tenant list response."""
    tenants: List[TenantResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TenantStatsResponse(BaseModel):
    """Tenant usage statistics."""
    tenant_id: str
    total_documents: int
    total_chunks: int
    total_queries: int
    storage_used_mb: float
    storage_limit_mb: int
    document_limit: int
