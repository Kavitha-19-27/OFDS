"""
Document Access Control model for fine-grained document permissions.
Supports user-level and role-level access restrictions.
"""
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AccessLevel(str, Enum):
    """Document access levels."""
    READ = "READ"
    WRITE = "WRITE"
    NONE = "NONE"


class DocumentAccess(BaseModel):
    """
    Document access control model.
    Defines who can access specific documents.
    """
    __tablename__ = "document_access"
    
    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # User-specific access (NULL means role-based only)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Role-based access (e.g., 'ADMIN', 'USER')
    role_access = Column(String(20), nullable=True)
    
    # Access level
    access_level = Column(
        SQLEnum(AccessLevel),
        default=AccessLevel.READ,
        nullable=False
    )
    
    # Who granted this access
    granted_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Optional expiration
    expires_at = Column(String(50), nullable=True)  # ISO datetime string
    
    # Relationships
    document = relationship("Document", backref="access_controls")
    user = relationship("User", foreign_keys=[user_id], backref="document_access")
    grantor = relationship("User", foreign_keys=[granted_by])
    
    def __repr__(self) -> str:
        return f"<DocumentAccess(doc={self.document_id}, user={self.user_id}, level={self.access_level})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if access has expired."""
        if not self.expires_at:
            return False
        from datetime import datetime
        try:
            exp_date = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.now(exp_date.tzinfo) > exp_date
        except:
            return False
