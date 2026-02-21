"""
Chat schemas for RAG interactions.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request with user question."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation threading"
    )
    top_k: Optional[int] = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of chunks to retrieve"
    )
    language_mode: Literal["english", "tanglish"] = Field(
        default="english",
        description="Language mode for AI responses - 'english' or 'tanglish'"
    )


class SourceChunk(BaseModel):
    """Source chunk information included in response."""
    chunk_id: str
    document_id: str
    document_name: str
    content_preview: str = Field(..., description="First 200 chars of chunk")
    page_number: Optional[int]
    relevance_score: float


class ChatResponse(BaseModel):
    """Chat response with answer and sources."""
    answer: str
    question: str
    session_id: str
    sources: List[SourceChunk] = Field(
        default_factory=list,
        description="Retrieved source chunks"
    )
    model_used: str
    tokens_used: int
    latency_ms: int


class ChatHistoryItem(BaseModel):
    """Single chat history item."""
    id: str
    question: str
    answer: str
    session_id: str
    created_at: datetime
    sources: Optional[List[SourceChunk]] = None
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response with pagination."""
    history: List[ChatHistoryItem]
    total: int
    page: int
    page_size: int
    pages: int


class ChatSessionResponse(BaseModel):
    """Chat session summary."""
    session_id: str
    message_count: int
    first_message: datetime
    last_message: datetime


class ChatSessionsListResponse(BaseModel):
    """List of chat sessions."""
    sessions: List[ChatSessionResponse]
    total: int
