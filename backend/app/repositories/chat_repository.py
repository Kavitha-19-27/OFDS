"""
Chat log repository for conversation history.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_log import ChatLog
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatLog]):
    """Repository for ChatLog model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ChatLog, session)
    
    async def get_by_session(
        self,
        session_id: str,
        tenant_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatLog]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Chat session ID
            tenant_id: Tenant ID
            skip: Records to skip
            limit: Max records
            
        Returns:
            List of chat logs ordered by time
        """
        query = (
            select(ChatLog)
            .where(
                and_(
                    ChatLog.session_id == session_id,
                    ChatLog.tenant_id == tenant_id
                )
            )
            .order_by(ChatLog.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_history(
        self,
        user_id: str,
        tenant_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatLog]:
        """
        Get chat history for a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            skip: Records to skip
            limit: Max records
            
        Returns:
            List of chat logs
        """
        query = (
            select(ChatLog)
            .where(
                and_(
                    ChatLog.user_id == user_id,
                    ChatLog.tenant_id == tenant_id
                )
            )
            .order_by(ChatLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_sessions(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[dict]:
        """
        Get unique chat sessions for a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            List of session summaries
        """
        query = (
            select(
                ChatLog.session_id,
                func.count(ChatLog.id).label('message_count'),
                func.min(ChatLog.created_at).label('first_message'),
                func.max(ChatLog.created_at).label('last_message')
            )
            .where(
                and_(
                    ChatLog.user_id == user_id,
                    ChatLog.tenant_id == tenant_id
                )
            )
            .group_by(ChatLog.session_id)
            .order_by(func.max(ChatLog.created_at).desc())
        )
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                "session_id": row.session_id,
                "message_count": row.message_count,
                "first_message": row.first_message,
                "last_message": row.last_message
            }
            for row in rows
        ]
    
    async def count_by_tenant(
        self,
        tenant_id: str,
        since: Optional[datetime] = None
    ) -> int:
        """
        Count chat logs for a tenant.
        
        Args:
            tenant_id: Tenant ID
            since: Optional start date
            
        Returns:
            Log count
        """
        query = select(func.count(ChatLog.id)).where(
            ChatLog.tenant_id == tenant_id
        )
        
        if since:
            query = query.where(ChatLog.created_at >= since)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_total_tokens_used(
        self,
        tenant_id: str,
        since: Optional[datetime] = None
    ) -> int:
        """
        Get total tokens used by a tenant.
        
        Args:
            tenant_id: Tenant ID
            since: Optional start date
            
        Returns:
            Total tokens
        """
        query = select(func.sum(ChatLog.tokens_used)).where(
            ChatLog.tenant_id == tenant_id
        )
        
        if since:
            query = query.where(ChatLog.created_at >= since)
        
        result = await self.session.execute(query)
        return result.scalar_one() or 0
    
    async def get_average_latency(
        self,
        tenant_id: str,
        days: int = 7
    ) -> float:
        """
        Get average response latency for a tenant.
        
        Args:
            tenant_id: Tenant ID
            days: Number of days to look back
            
        Returns:
            Average latency in ms
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(func.avg(ChatLog.latency_ms)).where(
            and_(
                ChatLog.tenant_id == tenant_id,
                ChatLog.created_at >= since
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one() or 0.0
    
    async def delete_old_logs(
        self,
        tenant_id: str,
        older_than_days: int = 90
    ) -> int:
        """
        Delete old chat logs for a tenant.
        
        Args:
            tenant_id: Tenant ID
            older_than_days: Delete logs older than this
            
        Returns:
            Number of deleted logs
        """
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        
        query = select(ChatLog).where(
            and_(
                ChatLog.tenant_id == tenant_id,
                ChatLog.created_at < cutoff
            )
        )
        result = await self.session.execute(query)
        logs = list(result.scalars().all())
        
        count = len(logs)
        for log in logs:
            await self.session.delete(log)
        
        await self.session.flush()
        return count
