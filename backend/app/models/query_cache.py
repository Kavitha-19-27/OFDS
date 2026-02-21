"""
Query Cache model for caching RAG responses.
Reduces Groq API calls and improves response time.
"""
from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey
from datetime import datetime, timedelta

from app.models.base import BaseModel


class QueryCache(BaseModel):
    """
    Query cache model for storing and retrieving cached responses.
    Essential for Groq free tier optimization.
    """
    __tablename__ = "query_cache"
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Query hash for fast lookup (SHA-256 of normalized query)
    query_hash = Column(
        String(64),
        nullable=False,
        index=True
    )
    
    # Original query text
    query_text = Column(Text, nullable=False)
    
    # Cached response as JSON
    response_json = Column(JSON, nullable=False)
    
    # Cache statistics
    hit_count = Column(Integer, default=0, nullable=False)
    
    # Expiration (ISO datetime string)
    expires_at = Column(String(50), nullable=False)
    
    # Document hash to invalidate when docs change
    document_hash = Column(String(64), nullable=True)
    
    def __repr__(self) -> str:
        return f"<QueryCache(query_hash={self.query_hash[:8]}..., hits={self.hit_count})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        try:
            exp_date = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() > exp_date.replace(tzinfo=None)
        except:
            return True
    
    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hit_count += 1
    
    @classmethod
    def create_entry(
        cls,
        tenant_id: str,
        query_hash: str,
        query_text: str,
        response_json: dict,
        ttl_hours: int = 1,
        document_hash: str = None
    ) -> "QueryCache":
        """Factory method to create cache entry with expiration."""
        expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat() + 'Z'
        return cls(
            tenant_id=tenant_id,
            query_hash=query_hash,
            query_text=query_text,
            response_json=response_json,
            expires_at=expires_at,
            document_hash=document_hash
        )
