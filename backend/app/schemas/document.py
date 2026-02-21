"""
Document schemas for file upload and management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    """Base document schema."""
    original_name: str
    file_size: int
    mime_type: str


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    tenant_id: str
    uploaded_by: Optional[str]
    filename: str
    original_name: str
    file_size: int
    file_hash: str
    mime_type: str
    status: DocumentStatus
    page_count: int
    chunk_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Computed
    file_size_mb: Optional[float] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated document list response."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: str
    filename: str
    original_name: str
    status: DocumentStatus
    message: str = "Document uploaded successfully"


class DocumentChunkResponse(BaseModel):
    """Document chunk response schema."""
    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int]
    
    class Config:
        from_attributes = True


class DocumentProcessingStatus(BaseModel):
    """Document processing status response."""
    document_id: str
    status: DocumentStatus
    page_count: int
    chunk_count: int
    error_message: Optional[str]
    progress_percent: Optional[int] = None


class RebuildIndexRequest(BaseModel):
    """Request to rebuild FAISS index."""
    document_ids: Optional[List[str]] = Field(
        None,
        description="Specific documents to reindex. If empty, rebuilds entire tenant index."
    )


class RebuildIndexResponse(BaseModel):
    """Response after index rebuild."""
    success: bool
    documents_processed: int
    chunks_indexed: int
    message: str


class DocumentStatsResponse(BaseModel):
    """Document statistics response."""
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(0, description="Total number of chunks")
    total_storage_bytes: int = Field(0, description="Total storage used in bytes")
    total_storage_mb: float = Field(0.0, description="Total storage used in MB")
    documents_by_status: dict = Field(default_factory=dict, description="Document count by status")
    processing_documents: int = Field(0, description="Documents currently processing")
    failed_documents: int = Field(0, description="Documents that failed processing")
