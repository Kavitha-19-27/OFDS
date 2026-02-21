"""
Audit Log model for tracking all system actions.
Provides complete audit trail for compliance and debugging.
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """
    Audit log model for tracking all actions in the system.
    Critical for security, compliance, and debugging.
    """
    __tablename__ = "audit_logs"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Action type
    action = Column(
        String(50),
        nullable=False,
        index=True
    )
    # Actions: LOGIN, LOGOUT, DOCUMENT_UPLOAD, DOCUMENT_DELETE, 
    #          CHAT_QUERY, USER_CREATE, USER_UPDATE, ACCESS_GRANT, etc.
    
    # Resource information
    resource_type = Column(String(50), nullable=True)  # DOCUMENT, CHAT, USER, etc.
    resource_id = Column(String(36), nullable=True)
    
    # Additional details as JSON
    details = Column(JSON, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Optional: status of the action
    status = Column(String(20), default="SUCCESS")  # SUCCESS, FAILED, DENIED
    
    # Relationships
    user = relationship("User", backref="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, user={self.user_id}, resource={self.resource_type})>"
    
    @classmethod
    def create_log(
        cls,
        tenant_id: str,
        action: str,
        user_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        status: str = "SUCCESS"
    ) -> "AuditLog":
        """Factory method for creating audit log entries."""
        return cls(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
