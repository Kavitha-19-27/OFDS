"""
Quota management service for tenant resource limits.
Enforces usage limits to prevent abuse and manage resources.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.tenant_quota import TenantQuota
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuotaExceededError(Exception):
    """Raised when a quota limit is exceeded."""
    def __init__(self, quota_type: str, limit: int, current: int):
        self.quota_type = quota_type
        self.limit = limit
        self.current = current
        super().__init__(f"{quota_type} quota exceeded: {current}/{limit}")


class QuotaService:
    """
    Service for managing tenant quotas and usage limits.
    """
    
    # Default quotas (adjust based on tier)
    DEFAULT_QUOTAS = {
        'free': {
            'max_documents': 10,
            'max_storage_mb': 50,
            'max_queries_per_day': 50,
            'max_tokens_per_day': 50000,
            'max_users': 1
        },
        'starter': {
            'max_documents': 100,
            'max_storage_mb': 500,
            'max_queries_per_day': 500,
            'max_tokens_per_day': 500000,
            'max_users': 5
        },
        'professional': {
            'max_documents': 1000,
            'max_storage_mb': 5000,
            'max_queries_per_day': 5000,
            'max_tokens_per_day': 5000000,
            'max_users': 50
        }
    }
    
    async def get_or_create_quota(
        self,
        db: AsyncSession,
        tenant_id: str,
        tier: str = 'free'
    ) -> TenantQuota:
        """
        Get existing quota or create with defaults.
        """
        result = await db.execute(
            select(TenantQuota).where(TenantQuota.tenant_id == tenant_id)
        )
        quota = result.scalar_one_or_none()
        
        if quota:
            return quota
        
        # Create new quota with tier defaults
        defaults = self.DEFAULT_QUOTAS.get(tier, self.DEFAULT_QUOTAS['free'])
        
        quota = TenantQuota(
            tenant_id=tenant_id,
            max_documents=defaults['max_documents'],
            max_storage_mb=defaults['max_storage_mb'],
            max_queries_per_day=defaults['max_queries_per_day'],
            max_tokens_per_day=defaults['max_tokens_per_day'],
            current_documents=0,
            current_storage_mb=0,
            queries_today=0,
            tokens_today=0,
            queries_reset_at=datetime.utcnow().isoformat()
        )
        
        db.add(quota)
        await db.commit()
        await db.refresh(quota)
        
        logger.info(f"Created {tier} quota for tenant {tenant_id}")
        return quota
    
    async def check_quota(
        self,
        db: AsyncSession,
        tenant_id: str,
        quota_type: str,
        amount: int = 1
    ) -> bool:
        """
        Check if an action is allowed within quota.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            quota_type: Type of quota (documents, storage_mb, queries, tokens)
            amount: Amount to check/consume
            
        Returns:
            True if within quota, raises QuotaExceededError if not
        """
        quota = await self.get_or_create_quota(db, tenant_id)
        
        # Reset daily counters if needed
        await self._maybe_reset_daily_counters(db, quota)
        
        # Check specific quota
        if quota_type == 'documents':
            if quota.current_documents + amount > quota.max_documents:
                raise QuotaExceededError(
                    'documents', quota.max_documents, quota.current_documents
                )
        
        elif quota_type == 'storage_mb':
            if quota.current_storage_mb + amount > quota.max_storage_mb:
                raise QuotaExceededError(
                    'storage_mb', quota.max_storage_mb, quota.current_storage_mb
                )
        
        elif quota_type == 'queries':
            if quota.queries_today + amount > quota.max_queries_per_day:
                raise QuotaExceededError(
                    'queries_per_day', quota.max_queries_per_day, quota.queries_today
                )
        
        elif quota_type == 'tokens':
            if quota.tokens_today + amount > quota.max_tokens_per_day:
                raise QuotaExceededError(
                    'tokens_per_day', quota.max_tokens_per_day, quota.tokens_today
                )
        
        return True
    
    async def consume_quota(
        self,
        db: AsyncSession,
        tenant_id: str,
        quota_type: str,
        amount: int = 1
    ) -> TenantQuota:
        """
        Consume quota after successful operation.
        Call this after the action completes successfully.
        """
        quota = await self.get_or_create_quota(db, tenant_id)
        
        # Reset daily counters if needed
        await self._maybe_reset_daily_counters(db, quota)
        
        # Update appropriate counter
        if quota_type == 'documents':
            quota.current_documents = min(
                quota.current_documents + amount,
                quota.max_documents * 2  # Cap at 2x to prevent overflow
            )
        
        elif quota_type == 'storage_mb':
            quota.current_storage_mb = min(
                quota.current_storage_mb + amount,
                quota.max_storage_mb * 2
            )
        
        elif quota_type == 'queries':
            quota.queries_today += amount
        
        elif quota_type == 'tokens':
            quota.tokens_today += amount
        
        await db.commit()
        await db.refresh(quota)
        
        return quota
    
    async def release_quota(
        self,
        db: AsyncSession,
        tenant_id: str,
        quota_type: str,
        amount: int = 1
    ) -> TenantQuota:
        """
        Release quota (e.g., when document is deleted).
        """
        quota = await self.get_or_create_quota(db, tenant_id)
        
        if quota_type == 'documents':
            quota.current_documents = max(0, quota.current_documents - amount)
        
        elif quota_type == 'storage_mb':
            quota.current_storage_mb = max(0, quota.current_storage_mb - amount)
        
        await db.commit()
        await db.refresh(quota)
        
        return quota
    
    async def get_quota_status(
        self,
        db: AsyncSession,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Get current quota status for tenant.
        """
        quota = await self.get_or_create_quota(db, tenant_id)
        await self._maybe_reset_daily_counters(db, quota)
        
        return {
            'documents': {
                'used': quota.current_documents,
                'limit': quota.max_documents,
                'remaining': max(0, quota.max_documents - quota.current_documents),
                'percentage': round(quota.current_documents / quota.max_documents * 100, 1)
            },
            'storage_mb': {
                'used': quota.current_storage_mb,
                'limit': quota.max_storage_mb,
                'remaining': max(0, quota.max_storage_mb - quota.current_storage_mb),
                'percentage': round(quota.current_storage_mb / quota.max_storage_mb * 100, 1)
            },
            'queries_today': {
                'used': quota.queries_today,
                'limit': quota.max_queries_per_day,
                'remaining': max(0, quota.max_queries_per_day - quota.queries_today),
                'percentage': round(quota.queries_today / quota.max_queries_per_day * 100, 1)
            },
            'tokens_today': {
                'used': quota.tokens_today,
                'limit': quota.max_tokens_per_day,
                'remaining': max(0, quota.max_tokens_per_day - quota.tokens_today),
                'percentage': round(quota.tokens_today / quota.max_tokens_per_day * 100, 1)
            },
            'resets_at': self._get_next_reset_time().isoformat()
        }
    
    async def update_quota_limits(
        self,
        db: AsyncSession,
        tenant_id: str,
        tier: Optional[str] = None,
        **limits
    ) -> TenantQuota:
        """
        Update quota limits for a tenant.
        Can use a tier preset or custom values.
        """
        quota = await self.get_or_create_quota(db, tenant_id)
        
        if tier and tier in self.DEFAULT_QUOTAS:
            defaults = self.DEFAULT_QUOTAS[tier]
            quota.max_documents = defaults['max_documents']
            quota.max_storage_mb = defaults['max_storage_mb']
            quota.max_queries_per_day = defaults['max_queries_per_day']
            quota.max_tokens_per_day = defaults['max_tokens_per_day']
        
        # Apply custom limits
        if 'max_documents' in limits:
            quota.max_documents = limits['max_documents']
        if 'max_storage_mb' in limits:
            quota.max_storage_mb = limits['max_storage_mb']
        if 'max_queries_per_day' in limits:
            quota.max_queries_per_day = limits['max_queries_per_day']
        if 'max_tokens_per_day' in limits:
            quota.max_tokens_per_day = limits['max_tokens_per_day']
        
        await db.commit()
        await db.refresh(quota)
        
        logger.info(f"Updated quota limits for tenant {tenant_id}")
        return quota
    
    async def _maybe_reset_daily_counters(
        self,
        db: AsyncSession,
        quota: TenantQuota
    ) -> None:
        """Reset daily counters if it's a new day."""
        today = datetime.utcnow().date()
        
        # Parse the last reset date from queries_reset_at string
        last_reset_date = None
        if quota.queries_reset_at:
            try:
                last_reset_dt = datetime.fromisoformat(quota.queries_reset_at)
                last_reset_date = last_reset_dt.date()
            except (ValueError, TypeError):
                pass
        
        if last_reset_date != today:
            quota.queries_today = 0
            quota.tokens_today = 0
            quota.queries_reset_at = datetime.utcnow().isoformat()
            await db.commit()
            logger.debug(f"Reset daily counters for tenant {quota.tenant_id}")
    
    def _get_next_reset_time(self) -> datetime:
        """Get when daily quotas will reset."""
        now = datetime.utcnow()
        tomorrow = now.date() + timedelta(days=1)
        return datetime.combine(tomorrow, datetime.min.time())
