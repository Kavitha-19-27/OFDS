"""
Tenant model for multi-tenancy support.
Each tenant represents a company/organization.
"""
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Tenant(BaseModel):
    """
    Tenant model representing an organization.
    All other resources are scoped to a tenant.
    """
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Resource limits
    max_documents = Column(Integer, default=100, nullable=False)
    max_storage_mb = Column(Integer, default=500, nullable=False)
    
    # Relationships
    users = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    documents = relationship(
        "Document",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, slug={self.slug})>"
    
    @property
    def max_storage_bytes(self) -> int:
        """Convert max storage from MB to bytes."""
        return self.max_storage_mb * 1024 * 1024
