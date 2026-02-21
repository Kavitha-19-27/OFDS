"""
Tenant management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_admin, get_current_tenant_admin
from app.core.exceptions import (
    DuplicateResourceError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.user import User, UserRole
from app.schemas.tenant import (
    TenantUpdate,
    TenantResponse,
    TenantStatsResponse,
    TenantListResponse,
)
from app.services.tenant_service import TenantService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get(
    "/current",
    response_model=TenantResponse,
    summary="Get current tenant info"
)
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about the current user's tenant.
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(current_user.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        max_documents=tenant.max_documents,
        max_storage_mb=tenant.max_storage_mb,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.get(
    "/current/stats",
    response_model=TenantStatsResponse,
    summary="Get current tenant statistics"
)
async def get_current_tenant_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for the current tenant.
    
    Includes document count, storage usage, and query counts.
    """
    tenant_service = TenantService(db)
    stats = await tenant_service.get_tenant_stats(current_user.tenant_id)
    
    return stats


@router.patch(
    "/current",
    response_model=TenantResponse,
    summary="Update current tenant"
)
async def update_current_tenant(
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current tenant's information.
    
    Only tenant admins can update tenant info.
    Only name can be updated by tenant admins.
    """
    tenant_service = TenantService(db)
    
    # Non-super admins can only update name
    update_data = {"name": tenant_data.name} if tenant_data.name else {}
    
    if current_user.role == UserRole.ADMIN:
        # Super admins can update limits
        if tenant_data.max_documents is not None:
            update_data["max_documents"] = tenant_data.max_documents
        if tenant_data.max_storage_mb is not None:
            update_data["max_storage_mb"] = tenant_data.max_storage_mb
    
    try:
        tenant = await tenant_service.update_tenant(
            current_user.tenant_id,
            **update_data
        )
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        logger.info(
            "Tenant updated",
            tenant_id=tenant.id,
            updated_by=current_user.id
        )
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            is_active=tenant.is_active,
            max_documents=tenant.max_documents,
            max_storage_mb=tenant.max_storage_mb,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
    except DuplicateResourceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


# ==================== Admin-only endpoints ====================

@router.get(
    "",
    response_model=TenantListResponse,
    summary="List all tenants (admin only)"
)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tenants in the system.
    
    Only system admins can access this endpoint.
    """
    tenant_service = TenantService(db)
    
    skip = (page - 1) * page_size
    tenants = await tenant_service.list_tenants(skip=skip, limit=page_size)
    total = await tenant_service.count_tenants()
    pages = (total + page_size - 1) // page_size
    
    return TenantListResponse(
        tenants=[
            TenantResponse(
                id=t.id,
                name=t.name,
                slug=t.slug,
                is_active=t.is_active,
                max_documents=t.max_documents,
                max_storage_mb=t.max_storage_mb,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
            for t in tenants
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID (admin only)"
)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific tenant by ID.
    
    Only system admins can access this endpoint.
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        max_documents=tenant.max_documents,
        max_storage_mb=tenant.max_storage_mb,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.get(
    "/{tenant_id}/stats",
    response_model=TenantStatsResponse,
    summary="Get tenant statistics (admin only)"
)
async def get_tenant_stats(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for a specific tenant.
    
    Only system admins can access this endpoint.
    """
    tenant_service = TenantService(db)
    
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    stats = await tenant_service.get_tenant_stats(tenant_id)
    return TenantStatsResponse(**stats)


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantResponse,
    summary="Suspend tenant (admin only)"
)
async def suspend_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Suspend a tenant account.
    
    Suspended tenants cannot access the system.
    Only system admins can suspend tenants.
    """
    if tenant_id == current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend your own tenant"
        )
    
    tenant_service = TenantService(db)
    tenant = await tenant_service.suspend_tenant(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    logger.info(
        "Tenant suspended",
        tenant_id=tenant_id,
        suspended_by=current_user.id
    )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        max_documents=tenant.max_documents,
        max_storage_mb=tenant.max_storage_mb,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    summary="Activate tenant (admin only)"
)
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a suspended tenant account.
    
    Only system admins can activate tenants.
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.activate_tenant(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    logger.info(
        "Tenant activated",
        tenant_id=tenant_id,
        activated_by=current_user.id
    )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        max_documents=tenant.max_documents,
        max_storage_mb=tenant.max_storage_mb,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.patch(
    "/{tenant_id}/limits",
    response_model=TenantResponse,
    summary="Update tenant limits (admin only)"
)
async def update_tenant_limits(
    tenant_id: str,
    max_documents: int = Query(None, ge=1, description="Maximum documents"),
    max_storage_mb: int = Query(None, ge=1, description="Maximum storage in MB"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update resource limits for a tenant.
    
    Only system admins can update limits.
    """
    tenant_service = TenantService(db)
    
    update_data = {}
    if max_documents is not None:
        update_data["max_documents"] = max_documents
    if max_storage_mb is not None:
        update_data["max_storage_mb"] = max_storage_mb
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No limits specified to update"
        )
    
    tenant = await tenant_service.update_tenant(tenant_id, **update_data)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    logger.info(
        "Tenant limits updated",
        tenant_id=tenant_id,
        updated_by=current_user.id,
        limits=update_data
    )
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        max_documents=tenant.max_documents,
        max_storage_mb=tenant.max_storage_mb,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )
