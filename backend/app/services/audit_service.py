"""
Audit logging service for tracking user actions.
Enterprise-grade audit trail for compliance and debugging.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete

from app.models.audit_log import AuditLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuditService:
    """
    Service for logging and querying audit events.
    All tenant actions are tracked for compliance.
    """
    
    # Action types
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_DOCUMENT_UPLOAD = "document_upload"
    ACTION_DOCUMENT_DELETE = "document_delete"
    ACTION_DOCUMENT_VIEW = "document_view"
    ACTION_CHAT_QUERY = "chat_query"
    ACTION_SETTINGS_CHANGE = "settings_change"
    ACTION_USER_CREATE = "user_create"
    ACTION_USER_DELETE = "user_delete"
    ACTION_PERMISSION_CHANGE = "permission_change"
    ACTION_EXPORT = "export"
    
    async def log_action(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            db: Database session
            tenant_id: Tenant performing action
            user_id: User performing action
            action: Action type (use constants above)
            resource_type: Type of resource affected (document, user, etc.)
            resource_id: ID of affected resource
            details: Additional action details (JSON)
            ip_address: Client IP
            user_agent: Client user agent
            
        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        logger.debug(f"Audit: {action} by user {user_id} on {resource_type}:{resource_id}")
        return audit_log
    
    async def get_audit_logs(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.
        """
        conditions = [AuditLog.tenant_id == tenant_id]
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)
        
        result = await db.execute(
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        return list(result.scalars().all())
    
    async def get_user_activity(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get activity summary for a user.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get logs
        logs = await self.get_audit_logs(
            db, tenant_id, user_id=user_id,
            start_date=start_date, limit=1000
        )
        
        # Aggregate by action
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        # Get last activity
        last_activity = logs[0].created_at if logs else None
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_actions': len(logs),
            'action_breakdown': action_counts,
            'last_activity': last_activity.isoformat() if last_activity else None
        }
    
    async def get_tenant_activity_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get activity summary for entire tenant.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Count by action type
        result = await db.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            )
            .where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.created_at >= start_date
                )
            )
            .group_by(AuditLog.action)
        )
        action_counts = {row.action: row.count for row in result.all()}
        
        # Count unique users
        result = await db.execute(
            select(func.count(func.distinct(AuditLog.user_id)))
            .where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.created_at >= start_date
                )
            )
        )
        active_users = result.scalar() or 0
        
        # Daily activity
        result = await db.execute(
            select(
                func.date(AuditLog.created_at).label('date'),
                func.count(AuditLog.id).label('count')
            )
            .where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.created_at >= start_date
                )
            )
            .group_by(func.date(AuditLog.created_at))
            .order_by(func.date(AuditLog.created_at))
        )
        daily_activity = {str(row.date): row.count for row in result.all()}
        
        return {
            'tenant_id': tenant_id,
            'period_days': days,
            'active_users': active_users,
            'total_actions': sum(action_counts.values()),
            'action_breakdown': action_counts,
            'daily_activity': daily_activity
        }
    
    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        tenant_id: str,
        retention_days: int = 90
    ) -> int:
        """
        Clean up audit logs older than retention period.
        
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        result = await db.execute(
            delete(AuditLog).where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.created_at < cutoff_date
                )
            )
        )
        
        await db.commit()
        
        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} audit logs for tenant {tenant_id}")
        return deleted
    
    async def export_audit_logs(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Export audit logs for compliance reporting.
        """
        logs = await self.get_audit_logs(
            db, tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        return [
            {
                'id': log.id,
                'timestamp': log.created_at.isoformat(),
                'user_id': log.user_id,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'details': log.details,
                'ip_address': log.ip_address
            }
            for log in logs
        ]
