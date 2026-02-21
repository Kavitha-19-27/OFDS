"""
User model with role-based access control.
Users belong to a tenant and have specific roles.
"""
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TenantScopedMixin


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "ADMIN"              # System admin
    USER = "USER"                # Regular user


class User(BaseModel, TenantScopedMixin):
    """
    User model with tenant scoping.
    Email must be unique within a tenant.
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
    
    # Use ForeignKey for tenant relationship
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    role = Column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        nullable=False
    )
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship(
        "Document",
        back_populates="uploader",
        lazy="selectin"
    )
    chat_logs = relationship(
        "ChatLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == UserRole.ADMIN
