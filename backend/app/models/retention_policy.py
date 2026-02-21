"""
Retention Policy model for data cleanup scheduling.
Enables automated cleanup of old data per tenant.
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey

from app.models.base import BaseModel


class RetentionPolicy(BaseModel):
    """
    Retention policy model for scheduling data cleanup.
    Ensures compliance and storage optimization.
    """
    __tablename__ = "retention_policies"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Resource type this policy applies to
    resource_type = Column(
        String(50),
        nullable=False,
        index=True
    )
    # Types: CHAT_LOGS, AUDIT_LOGS, QUERY_CACHE, RETRIEVAL_METRICS
    
    # Retention period in days
    retention_days = Column(Integer, nullable=False)
    
    # Is this policy active?
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Last cleanup timestamp (ISO string)
    last_cleanup_at = Column(String(50), nullable=True)
    
    # Records deleted in last cleanup
    last_cleanup_count = Column(Integer, default=0, nullable=False)
    
    def __repr__(self) -> str:
        return f"<RetentionPolicy(tenant={self.tenant_id}, type={self.resource_type}, days={self.retention_days})>"


# Default retention policies to be created for new tenants
DEFAULT_RETENTION_POLICIES = [
    {
        "resource_type": "CHAT_LOGS",
        "retention_days": 90,
        "is_active": True
    },
    {
        "resource_type": "AUDIT_LOGS",
        "retention_days": 365,
        "is_active": True
    },
    {
        "resource_type": "QUERY_CACHE",
        "retention_days": 7,
        "is_active": True
    },
    {
        "resource_type": "RETRIEVAL_METRICS",
        "retention_days": 30,
        "is_active": True
    }
]
