"""
Base model with common fields and utilities.
Provides timestamp tracking and UUID generation.
"""
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declared_attr

from app.database import Base


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )


class TenantScopedMixin:
    """
    Mixin for models that belong to a tenant.
    Ensures all queries can be scoped to a specific tenant.
    """
    
    @declared_attr
    def tenant_id(cls):
        return Column(
            String(36),
            nullable=False,
            index=True
        )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with UUID primary key and timestamps.
    All models should inherit from this.
    """
    __abstract__ = True
    
    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
