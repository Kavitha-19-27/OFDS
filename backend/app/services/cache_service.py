"""
Cache service for query result caching.
Critical for Groq free tier optimization - reduces API calls.
"""
import hashlib
import json
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.query_cache import QueryCache
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Service for caching RAG query results.
    Reduces Groq API calls by serving cached responses.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.default_ttl_hours = 1  # Cache for 1 hour
    
    @staticmethod
    def hash_query(query: str, tenant_id: str) -> str:
        """
        Generate hash for query lookup.
        Normalizes query before hashing for better cache hits.
        """
        # Normalize: lowercase, strip whitespace, remove punctuation variations
        normalized = query.lower().strip()
        # Remove common variations
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Include tenant_id in hash for isolation
        combined = f"{tenant_id}:{normalized}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    async def get_cached_response(
        self,
        tenant_id: str,
        query: str
    ) -> Optional[dict]:
        """
        Check if query response is cached.
        
        Returns:
            Cached response dict or None if not found/expired
        """
        query_hash = self.hash_query(query, tenant_id)
        
        result = await self.session.execute(
            select(QueryCache).where(
                QueryCache.tenant_id == tenant_id,
                QueryCache.query_hash == query_hash
            )
        )
        cache_entry = result.scalar_one_or_none()
        
        if cache_entry:
            if cache_entry.is_expired:
                # Clean up expired entry
                await self.session.delete(cache_entry)
                await self.session.commit()
                logger.debug("Cache entry expired", query_hash=query_hash[:8])
                return None
            
            # Record cache hit
            cache_entry.record_hit()
            await self.session.commit()
            
            logger.info(
                "Cache hit",
                query_hash=query_hash[:8],
                hit_count=cache_entry.hit_count
            )
            return cache_entry.response_json
        
        return None
    
    async def cache_response(
        self,
        tenant_id: str,
        query: str,
        response: dict,
        ttl_hours: int = None,
        document_hash: str = None
    ) -> None:
        """
        Cache a query response.
        
        Args:
            tenant_id: Tenant ID
            query: Original query text
            response: Response dict to cache
            ttl_hours: Time to live in hours (default: 1)
            document_hash: Hash of documents to invalidate on change
        """
        query_hash = self.hash_query(query, tenant_id)
        ttl = ttl_hours or self.default_ttl_hours
        
        # Check if entry exists
        result = await self.session.execute(
            select(QueryCache).where(
                QueryCache.tenant_id == tenant_id,
                QueryCache.query_hash == query_hash
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing entry
            existing.response_json = response
            existing.expires_at = (
                datetime.utcnow().replace(hour=datetime.utcnow().hour + ttl)
            ).isoformat() + 'Z'
            existing.document_hash = document_hash
        else:
            # Create new entry
            cache_entry = QueryCache.create_entry(
                tenant_id=tenant_id,
                query_hash=query_hash,
                query_text=query,
                response_json=response,
                ttl_hours=ttl,
                document_hash=document_hash
            )
            self.session.add(cache_entry)
        
        await self.session.commit()
        logger.info("Response cached", query_hash=query_hash[:8], ttl_hours=ttl)
    
    async def invalidate_tenant_cache(self, tenant_id: str) -> int:
        """
        Invalidate all cache entries for a tenant.
        Called when documents change.
        
        Returns:
            Number of entries deleted
        """
        result = await self.session.execute(
            delete(QueryCache).where(QueryCache.tenant_id == tenant_id)
        )
        await self.session.commit()
        
        count = result.rowcount
        logger.info("Cache invalidated", tenant_id=tenant_id, entries_deleted=count)
        return count
    
    async def invalidate_by_document_hash(
        self,
        tenant_id: str,
        document_hash: str
    ) -> int:
        """
        Invalidate cache entries related to specific documents.
        
        Returns:
            Number of entries deleted
        """
        result = await self.session.execute(
            delete(QueryCache).where(
                QueryCache.tenant_id == tenant_id,
                QueryCache.document_hash == document_hash
            )
        )
        await self.session.commit()
        
        count = result.rowcount
        logger.info(
            "Cache invalidated by document",
            tenant_id=tenant_id,
            document_hash=document_hash[:8],
            entries_deleted=count
        )
        return count
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        Should be run periodically.
        
        Returns:
            Number of entries deleted
        """
        now = datetime.utcnow().isoformat() + 'Z'
        
        result = await self.session.execute(
            delete(QueryCache).where(QueryCache.expires_at < now)
        )
        await self.session.commit()
        
        count = result.rowcount
        if count > 0:
            logger.info("Expired cache cleaned", entries_deleted=count)
        return count
    
    async def get_cache_stats(self, tenant_id: str) -> dict:
        """
        Get cache statistics for a tenant.
        """
        from sqlalchemy import func
        
        result = await self.session.execute(
            select(
                func.count(QueryCache.id).label('total_entries'),
                func.sum(QueryCache.hit_count).label('total_hits')
            ).where(QueryCache.tenant_id == tenant_id)
        )
        row = result.one()
        
        return {
            "total_entries": row.total_entries or 0,
            "total_hits": row.total_hits or 0
        }
