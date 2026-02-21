"""
Base repository pattern implementation.
Provides common CRUD operations with tenant scoping.
"""
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository base class.
    Provides standard CRUD operations with optional tenant scoping.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(
        self,
        id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[ModelType]:
        """
        Get record by ID, optionally scoped to tenant.
        
        Args:
            id: Record ID
            tenant_id: Optional tenant ID for scoping
            
        Returns:
            Model instance or None
        """
        query = select(self.model).where(self.model.id == id)
        
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        tenant_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            tenant_id: Optional tenant ID for scoping
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, tenant_id: Optional[str] = None) -> int:
        """
        Count total records.
        
        Args:
            tenant_id: Optional tenant ID for scoping
            
        Returns:
            Total count
        """
        query = select(func.count(self.model.id))
        
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def update(
        self,
        instance: ModelType,
        **kwargs: Any
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            instance: Model instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated model instance
        """
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def delete(self, instance: ModelType) -> bool:
        """
        Delete a record.
        
        Args:
            instance: Model instance to delete
            
        Returns:
            True if deleted successfully
        """
        await self.session.delete(instance)
        await self.session.flush()
        return True
    
    async def delete_by_id(
        self,
        id: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete record by ID.
        
        Args:
            id: Record ID
            tenant_id: Optional tenant ID for scoping
            
        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id, tenant_id)
        if instance:
            return await self.delete(instance)
        return False
    
    async def exists(
        self,
        id: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if record exists.
        
        Args:
            id: Record ID
            tenant_id: Optional tenant ID
            
        Returns:
            True if exists
        """
        instance = await self.get_by_id(id, tenant_id)
        return instance is not None
    
    async def bulk_create(self, items: List[dict]) -> List[ModelType]:
        """
        Create multiple records.
        
        Args:
            items: List of dictionaries with model field values
            
        Returns:
            List of created instances
        """
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        
        for instance in instances:
            await self.session.refresh(instance)
        
        return instances
    
    async def bulk_delete_by_tenant(self, tenant_id: str) -> int:
        """
        Delete all records for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Number of deleted records
        """
        if not hasattr(self.model, 'tenant_id'):
            raise ValueError("Model does not support tenant scoping")
        
        query = delete(self.model).where(self.model.tenant_id == tenant_id)
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount
