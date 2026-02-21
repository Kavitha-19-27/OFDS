"""
Retrieval Metrics model for quality monitoring.
Tracks search quality and response effectiveness.
"""
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Enum as SQLEnum, Boolean

from app.models.base import BaseModel


class ConfidenceLevel(str, Enum):
    """Confidence levels for responses."""
    HIGH = "HIGH"      # > 0.75
    MEDIUM = "MEDIUM"  # 0.5 - 0.75
    LOW = "LOW"        # < 0.5
    NONE = "NONE"      # No relevant chunks found


class RetrievalMetrics(BaseModel):
    """
    Retrieval metrics model for quality monitoring.
    Enables analysis and improvement of RAG pipeline.
    """
    __tablename__ = "retrieval_metrics"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    chat_log_id = Column(
        String(36),
        ForeignKey("chat_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=True)  # FACTUAL, SUMMARY, COMPARISON, etc.
    
    # Search metrics
    semantic_score_avg = Column(Float, nullable=True)
    semantic_score_max = Column(Float, nullable=True)
    bm25_score_avg = Column(Float, nullable=True)
    bm25_score_max = Column(Float, nullable=True)
    hybrid_score_avg = Column(Float, nullable=True)
    
    # Retrieval counts
    chunks_searched = Column(Integer, default=0, nullable=False)
    chunks_retrieved = Column(Integer, default=0, nullable=False)
    chunks_used = Column(Integer, default=0, nullable=False)
    
    # Confidence
    confidence_score = Column(Float, nullable=True)
    confidence_level = Column(
        SQLEnum(ConfidenceLevel),
        default=ConfidenceLevel.MEDIUM,
        nullable=False
    )
    
    # Response metrics
    response_tokens = Column(Integer, default=0, nullable=False)
    context_tokens = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    
    # Quality indicators from feedback
    response_helpful = Column(Boolean, nullable=True)  # From user feedback
    
    # Cache status
    was_cached = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f"<RetrievalMetrics(confidence={self.confidence_level}, score={self.confidence_score})>"
    
    @classmethod
    def calculate_confidence_level(cls, score: float) -> ConfidenceLevel:
        """Calculate confidence level from score."""
        if score >= 0.75:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif score > 0:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.NONE
