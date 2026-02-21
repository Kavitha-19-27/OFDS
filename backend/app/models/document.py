"""
Document and DocumentChunk models for file management.
Supports PDF upload, processing, and chunk storage.
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TenantScopedMixin


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(BaseModel, TenantScopedMixin):
    """
    Document model for uploaded files.
    Tracks processing status and metadata.
    """
    __tablename__ = "documents"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    uploaded_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # File information
    filename = Column(String(255), nullable=False)  # Stored filename (UUID-based)
    original_name = Column(String(255), nullable=False)  # Original upload name
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash for deduplication
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    
    # Processing status
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Metadata
    page_count = Column(Integer, default=0, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    uploader = relationship("User", back_populates="documents")
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DocumentChunk.chunk_index"
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.original_name}, status={self.status})>"
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_processed(self) -> bool:
        """Check if document has been processed."""
        return self.status == DocumentStatus.COMPLETED
    
    def mark_processing(self) -> None:
        """Mark document as processing."""
        self.status = DocumentStatus.PROCESSING
        self.error_message = None
    
    def mark_completed(self, page_count: int, chunk_count: int) -> None:
        """Mark document as successfully processed."""
        self.status = DocumentStatus.COMPLETED
        self.page_count = page_count
        self.chunk_count = chunk_count
        self.error_message = None
    
    def mark_failed(self, error: str) -> None:
        """Mark document as failed with error message."""
        self.status = DocumentStatus.FAILED
        self.error_message = error


class DocumentChunk(BaseModel, TenantScopedMixin):
    """
    Document chunk model for storing text segments.
    Each chunk has a corresponding embedding in FAISS.
    """
    __tablename__ = "document_chunks"
    
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
    
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    
    # Reference to FAISS index position
    embedding_id = Column(Integer, nullable=True, index=True)
    
    # Relationship
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, doc={self.document_id}, index={self.chunk_index})>"
