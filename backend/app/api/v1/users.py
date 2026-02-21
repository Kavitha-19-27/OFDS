"""
User management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_tenant_admin, verify_tenant_access
from app.core.exceptions import (
    DuplicateResourceError,
    ResourceNotFoundError,
    ValidationError,
    AuthorizationError,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from app.services.user_service import UserService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user in tenant"
)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user within the current tenant.
    
    Only tenant admins and above can create users.
    New users inherit the tenant of the creating admin.
    """
    user_service = UserService(db)
    
    try:
        # Prevent creating users with higher role than self
        if user_data.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create admin users"
            )
        
        user = await user_service.create_user(
            tenant_id=current_user.tenant_id,
            data=user_data,
            created_by_role=current_user.role
        )
        
        logger.info(
            "User created",
            user_id=user.id,
            email=user.email,
            created_by=current_user.id
        )
        
        return UserResponse.model_validate(user)
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


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users in tenant"
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in the current tenant.
    
    Only tenant admins can view user lists.
    Results are paginated.
    """
    user_service = UserService(db)
    
    return await user_service.get_users(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID"
)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific user by ID.
    
    Users can view their own profile.
    Tenant admins can view any user in their tenant.
    """
    user_service = UserService(db)
    
    # Check permissions
    if user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own profile"
        )
    
    user = await user_service.get_user(user_id, current_user.tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user"
)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's information.
    
    Users can update their own profile (except role).
    Tenant admins can update any user in their tenant.
    """
    user_service = UserService(db)
    
    # Check permissions
    is_self = user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own profile"
        )
    
    # Non-admins cannot change roles
    if not is_admin and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    try:
        user = await user_service.update_user(
            user_id=user_id,
            tenant_id=current_user.tenant_id,
            data=user_data,
            updated_by_role=current_user.role
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info("User updated", user_id=user_id, updated_by=current_user.id)
        
        return UserResponse.model_validate(user)
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


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user"
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user from the tenant.
    
    Only tenant admins can delete users.
    Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user_service = UserService(db)
    
    try:
        await user_service.delete_user(user_id, current_user.tenant_id)
        logger.info("User deleted", user_id=user_id, deleted_by=current_user.id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate user"
)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user account.
    
    Deactivated users cannot log in but their data is preserved.
    Only tenant admins can deactivate users.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user_service = UserService(db)
    
    user = await user_service.deactivate_user(user_id, current_user.tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info("User deactivated", user_id=user_id, deactivated_by=current_user.id)
    
    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user"
)
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a previously deactivated user account.
    
    Only tenant admins can activate users.
    """
    user_service = UserService(db)
    
    user = await user_service.activate_user(user_id, current_user.tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info("User activated", user_id=user_id, activated_by=current_user.id)
    
    return UserResponse.model_validate(user)
