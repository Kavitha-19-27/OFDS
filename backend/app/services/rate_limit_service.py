"""
Rate limiting service for managing API request rates.
Critical for Groq free tier compliance (30 RPM, 6000 TPM).
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import time

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, limit_type: str, retry_after: float):
        self.limit_type = limit_type
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {limit_type}. Retry after {retry_after}s")


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.
    Tracks both requests per minute (RPM) and tokens per minute (TPM).
    """
    
    def __init__(
        self,
        rpm_limit: int = 30,
        tpm_limit: int = 6000,
        window_seconds: int = 60
    ):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.window_seconds = window_seconds
        
        # Track requests and tokens per tenant
        self._request_timestamps: Dict[int, list] = {}
        self._token_counts: Dict[int, list] = {}  # (timestamp, tokens)
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        estimated_tokens: int = 0
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            # Clean old entries
            self._cleanup_old_entries(tenant_id, window_start)
            
            # Check RPM
            requests = self._request_timestamps.get(tenant_id, [])
            if len(requests) >= self.rpm_limit:
                retry_after = requests[0] - window_start
                return False, retry_after
            
            # Check TPM
            token_entries = self._token_counts.get(tenant_id, [])
            current_tokens = sum(t for _, t in token_entries)
            if current_tokens + estimated_tokens > self.tpm_limit:
                # Find when we'll have capacity
                if token_entries:
                    retry_after = token_entries[0][0] - window_start
                    return False, retry_after
            
            return True, None
    
    async def record_request(
        self,
        tenant_id: str,
        tokens_used: int = 0
    ) -> None:
        """Record a completed request for rate limiting."""
        async with self._lock:
            now = time.time()
            
            # Record request timestamp
            if tenant_id not in self._request_timestamps:
                self._request_timestamps[tenant_id] = []
            self._request_timestamps[tenant_id].append(now)
            
            # Record token usage
            if tokens_used > 0:
                if tenant_id not in self._token_counts:
                    self._token_counts[tenant_id] = []
                self._token_counts[tenant_id].append((now, tokens_used))
    
    def _cleanup_old_entries(self, tenant_id: str, window_start: float) -> None:
        """Remove entries outside the sliding window."""
        if tenant_id in self._request_timestamps:
            self._request_timestamps[tenant_id] = [
                ts for ts in self._request_timestamps[tenant_id]
                if ts > window_start
            ]
        
        if tenant_id in self._token_counts:
            self._token_counts[tenant_id] = [
                (ts, tokens) for ts, tokens in self._token_counts[tenant_id]
                if ts > window_start
            ]
    
    async def get_rate_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get current rate limit status for tenant."""
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            self._cleanup_old_entries(tenant_id, window_start)
            
            requests = self._request_timestamps.get(tenant_id, [])
            token_entries = self._token_counts.get(tenant_id, [])
            current_tokens = sum(t for _, t in token_entries)
            
            return {
                'rpm': {
                    'used': len(requests),
                    'limit': self.rpm_limit,
                    'remaining': max(0, self.rpm_limit - len(requests))
                },
                'tpm': {
                    'used': current_tokens,
                    'limit': self.tpm_limit,
                    'remaining': max(0, self.tpm_limit - current_tokens)
                },
                'window_seconds': self.window_seconds,
                'resets_in': self.window_seconds
            }


class RateLimitService:
    """
    Service for managing rate limits across tenants.
    """
    
    # Default Groq free tier limits
    GROQ_FREE_RPM = 30
    GROQ_FREE_TPM = 6000
    
    def __init__(self):
        # Global Groq API rate limiter (shared across all tenants)
        self.groq_limiter = RateLimiter(
            rpm_limit=self.GROQ_FREE_RPM,
            tpm_limit=self.GROQ_FREE_TPM
        )
        
        # Per-tenant limiters (for fair sharing)
        self._tenant_limiters: Dict[int, RateLimiter] = {}
    
    def get_tenant_limiter(
        self,
        tenant_id: str,
        rpm_share: float = 0.5  # Each tenant gets 50% of global limit
    ) -> RateLimiter:
        """Get or create rate limiter for tenant."""
        if tenant_id not in self._tenant_limiters:
            self._tenant_limiters[tenant_id] = RateLimiter(
                rpm_limit=int(self.GROQ_FREE_RPM * rpm_share),
                tpm_limit=int(self.GROQ_FREE_TPM * rpm_share)
            )
        return self._tenant_limiters[tenant_id]
    
    async def acquire(
        self,
        tenant_id: str,
        estimated_tokens: int = 500
    ) -> bool:
        """
        Acquire rate limit slot before making request.
        
        Raises:
            RateLimitExceededError if limits exceeded
        """
        # Check global limit first
        allowed, retry_after = await self.groq_limiter.check_rate_limit(
            0,  # Global tenant ID
            estimated_tokens
        )
        
        if not allowed:
            raise RateLimitExceededError('global_groq', retry_after)
        
        # Check tenant-specific limit
        tenant_limiter = self.get_tenant_limiter(tenant_id)
        allowed, retry_after = await tenant_limiter.check_rate_limit(
            tenant_id,
            estimated_tokens
        )
        
        if not allowed:
            raise RateLimitExceededError('tenant', retry_after)
        
        return True
    
    async def record(
        self,
        tenant_id: str,
        tokens_used: int
    ) -> None:
        """Record completed request for rate tracking."""
        # Record in global limiter
        await self.groq_limiter.record_request(0, tokens_used)
        
        # Record in tenant limiter
        tenant_limiter = self.get_tenant_limiter(tenant_id)
        await tenant_limiter.record_request(tenant_id, tokens_used)
    
    async def get_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get rate limit status for tenant."""
        global_status = await self.groq_limiter.get_rate_status(0)
        
        tenant_limiter = self.get_tenant_limiter(tenant_id)
        tenant_status = await tenant_limiter.get_rate_status(tenant_id)
        
        return {
            'global': global_status,
            'tenant': tenant_status
        }
    
    async def wait_for_capacity(
        self,
        tenant_id: str,
        estimated_tokens: int = 500,
        timeout: float = 30.0
    ) -> bool:
        """
        Wait until rate limit capacity is available.
        
        Returns:
            True if capacity acquired, False if timeout
        """
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                await self.acquire(tenant_id, estimated_tokens)
                return True
            except RateLimitExceededError as e:
                wait_time = min(e.retry_after, timeout - (time.time() - start))
                if wait_time <= 0:
                    return False
                logger.debug(f"Rate limit hit, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        return False
