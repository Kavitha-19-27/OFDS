"""
ChatLog model for storing conversation history.
Tracks queries, responses, and retrieval context.
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, TenantScopedMixin


class ChatLog(BaseModel, TenantScopedMixin):
    """
    Chat log model for storing RAG interactions.
    Helps with debugging, analytics, and conversation history.
    """
    __tablename__ = "chat_logs"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session tracking for conversation threads
    session_id = Column(String(36), nullable=False, index=True)
    
    # Q&A content
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # Retrieval context - stores chunk IDs and relevance scores
    context_chunks = Column(JSON, nullable=True)
    
    # Model information
    model_used = Column(String(50), nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="chat_logs")
    
    def __repr__(self) -> str:
        return f"<ChatLog(id={self.id}, user={self.user_id}, session={self.session_id})>"
    
    @property
    def latency_seconds(self) -> float:
        """Get latency in seconds."""
        return round(self.latency_ms / 1000, 2)
