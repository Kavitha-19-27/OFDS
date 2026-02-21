"""
Document Summary model for storing pre-generated summaries.
Reduces repeated LLM calls for common operations.
"""
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SummaryType(str, Enum):
    """Types of document summaries."""
    BRIEF = "BRIEF"        # ~100 tokens
    DETAILED = "DETAILED"  # ~500 tokens
    KEYWORDS = "KEYWORDS"  # Key phrases/topics
    OUTLINE = "OUTLINE"    # Document structure


class DocumentSummary(BaseModel):
    """
    Document summary model for caching generated summaries.
    One-time LLM cost per document.
    """
    __tablename__ = "document_summaries"
    
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
    
    # Summary type
    summary_type = Column(
        SQLEnum(SummaryType),
        nullable=False,
        index=True
    )
    
    # Summary content
    summary_text = Column(Text, nullable=False)
    
    # Token count for the summary
    token_count = Column(Integer, default=0, nullable=False)
    
    # Model used to generate
    model_used = Column(String(50), nullable=True)
    
    # Relationships
    document = relationship("Document", backref="summaries")
    
    def __repr__(self) -> str:
        return f"<DocumentSummary(doc={self.document_id}, type={self.summary_type})>"
