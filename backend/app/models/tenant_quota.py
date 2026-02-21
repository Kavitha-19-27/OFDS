"""
Tenant Quota model for managing usage limits per tenant.
Tracks documents, storage, and query quotas.
"""
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.models.base import BaseModel


class TenantQuota(BaseModel):
    """
    Tenant quota model for tracking and limiting resource usage.
    Enforces multi-tenant fair usage on Groq free tier.
    """
    __tablename__ = "tenant_quotas"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Document limits
    max_documents = Column(Integer, default=100, nullable=False)
    current_documents = Column(Integer, default=0, nullable=False)
    
    # Storage limits (MB)
    max_storage_mb = Column(Integer, default=500, nullable=False)
    current_storage_mb = Column(Float, default=0.0, nullable=False)
    
    # Query limits (per day)
    max_queries_per_day = Column(Integer, default=500, nullable=False)
    queries_today = Column(Integer, default=0, nullable=False)
    queries_reset_at = Column(String(50), nullable=True)  # ISO datetime
    
    # Query limits (per minute) - for rate limiting
    max_queries_per_minute = Column(Integer, default=10, nullable=False)
    
    # Token limits (per day) - for Groq optimization
    max_tokens_per_day = Column(Integer, default=50000, nullable=False)
    tokens_today = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", backref="quota")
    
    def __repr__(self) -> str:
        return f"<TenantQuota(tenant={self.tenant_id}, docs={self.current_documents}/{self.max_documents})>"
    
    @property
    def documents_remaining(self) -> int:
        """Get remaining document upload allowance."""
        return max(0, self.max_documents - self.current_documents)
    
    @property
    def storage_remaining_mb(self) -> float:
        """Get remaining storage in MB."""
        return max(0.0, self.max_storage_mb - self.current_storage_mb)
    
    @property
    def queries_remaining(self) -> int:
        """Get remaining queries for today."""
        self._check_reset()
        return max(0, self.max_queries_per_day - self.queries_today)
    
    @property
    def tokens_remaining(self) -> int:
        """Get remaining tokens for today."""
        self._check_reset()
        return max(0, self.max_tokens_per_day - self.tokens_today)
    
    def _check_reset(self) -> None:
        """Check if daily counters need to be reset."""
        if self.queries_reset_at:
            try:
                reset_time = datetime.fromisoformat(self.queries_reset_at.replace('Z', '+00:00'))
                if datetime.now(reset_time.tzinfo) > reset_time:
                    self.queries_today = 0
                    self.tokens_today = 0
                    self.queries_reset_at = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
            except:
                pass
    
    def can_upload_document(self, file_size_mb: float = 0) -> tuple[bool, str]:
        """Check if tenant can upload a document."""
        if self.current_documents >= self.max_documents:
            return False, f"Document limit reached ({self.max_documents})"
        if self.current_storage_mb + file_size_mb > self.max_storage_mb:
            return False, f"Storage limit reached ({self.max_storage_mb}MB)"
        return True, ""
    
    def can_query(self) -> tuple[bool, str]:
        """Check if tenant can make a query."""
        self._check_reset()
        if self.queries_today >= self.max_queries_per_day:
            return False, "Daily query limit reached"
        return True, ""
    
    def record_document_upload(self, file_size_mb: float) -> None:
        """Record a document upload."""
        self.current_documents += 1
        self.current_storage_mb += file_size_mb
    
    def record_document_delete(self, file_size_mb: float) -> None:
        """Record a document deletion."""
        self.current_documents = max(0, self.current_documents - 1)
        self.current_storage_mb = max(0.0, self.current_storage_mb - file_size_mb)
    
    def record_query(self, tokens_used: int = 0) -> None:
        """Record a query."""
        self._check_reset()
        self.queries_today += 1
        self.tokens_today += tokens_used
        if not self.queries_reset_at:
            self.queries_reset_at = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
