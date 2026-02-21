"""
Ingestion Queue model for async document processing.
Enables background processing with priority management.
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum as SQLEnum

from app.models.base import BaseModel


class QueueStatus(str, Enum):
    """Queue item status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class IngestionQueue(BaseModel):
    """
    Ingestion queue model for async document processing.
    Manages background processing workload.
    """
    __tablename__ = "ingestion_queue"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Priority (1 = highest, 10 = lowest)
    priority = Column(Integer, default=5, nullable=False, index=True)
    
    # Status
    status = Column(
        SQLEnum(QueueStatus),
        default=QueueStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Processing info
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    last_error = Column(Text, nullable=True)
    
    # Timestamps (ISO strings for SQLite compatibility)
    started_at = Column(String(50), nullable=True)
    completed_at = Column(String(50), nullable=True)
    
    # Worker info
    worker_id = Column(String(50), nullable=True)
    
    def __repr__(self) -> str:
        return f"<IngestionQueue(doc={self.document_id}, status={self.status}, priority={self.priority})>"
    
    @property
    def can_retry(self) -> bool:
        """Check if the item can be retried."""
        return self.attempts < self.max_attempts and self.status == QueueStatus.FAILED
    
    def mark_processing(self, worker_id: str = None) -> None:
        """Mark item as being processed."""
        from datetime import datetime
        self.status = QueueStatus.PROCESSING
        self.started_at = datetime.utcnow().isoformat() + 'Z'
        self.worker_id = worker_id
        self.attempts += 1
    
    def mark_completed(self) -> None:
        """Mark item as successfully completed."""
        from datetime import datetime
        self.status = QueueStatus.COMPLETED
        self.completed_at = datetime.utcnow().isoformat() + 'Z'
        self.last_error = None
    
    def mark_failed(self, error: str) -> None:
        """Mark item as failed."""
        from datetime import datetime
        self.status = QueueStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat() + 'Z'
        self.last_error = error
    
    def mark_pending_retry(self) -> None:
        """Reset to pending for retry."""
        self.status = QueueStatus.PENDING
        self.worker_id = None
