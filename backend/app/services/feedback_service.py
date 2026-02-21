"""
Feedback service for collecting and analyzing user feedback.
Tracks 👍/👎 ratings and comments on responses.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.chat_feedback import ChatFeedback
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackService:
    """
    Service for managing user feedback on chat responses.
    Used for quality monitoring and model improvement.
    """
    
    # Issue types for negative feedback
    ISSUE_INCORRECT = "incorrect"
    ISSUE_INCOMPLETE = "incomplete"
    ISSUE_IRRELEVANT = "irrelevant"
    ISSUE_OUTDATED = "outdated"
    ISSUE_UNCLEAR = "unclear"
    ISSUE_OTHER = "other"
    
    async def submit_feedback(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: int,
        message_id: int,
        session_id: int,
        rating: int,
        feedback_text: Optional[str] = None,
        issue_type: Optional[str] = None
    ) -> ChatFeedback:
        """
        Submit feedback for a chat response.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User submitting feedback
            message_id: Message being rated
            session_id: Chat session ID
            rating: 1 for 👍, -1 for 👎
            feedback_text: Optional text comment
            issue_type: Type of issue (for negative feedback)
            
        Returns:
            Created ChatFeedback entry
        """
        # Validate rating
        if rating not in [-1, 1]:
            raise ValueError("Rating must be -1 (thumbs down) or 1 (thumbs up)")
        
        # Check for existing feedback
        existing = await db.execute(
            select(ChatFeedback).where(
                and_(
                    ChatFeedback.tenant_id == tenant_id,
                    ChatFeedback.user_id == user_id,
                    ChatFeedback.message_id == message_id
                )
            )
        )
        existing_feedback = existing.scalar_one_or_none()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.rating = rating
            existing_feedback.feedback_text = feedback_text
            existing_feedback.issue_type = issue_type
            existing_feedback.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing_feedback)
            logger.debug(f"Updated feedback for message {message_id}")
            return existing_feedback
        
        # Create new feedback
        feedback = ChatFeedback(
            tenant_id=tenant_id,
            user_id=user_id,
            message_id=message_id,
            session_id=session_id,
            rating=rating,
            feedback_text=feedback_text,
            issue_type=issue_type
        )
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        logger.info(f"Recorded {'positive' if rating > 0 else 'negative'} feedback for message {message_id}")
        return feedback
    
    async def get_feedback(
        self,
        db: AsyncSession,
        tenant_id: str,
        message_id: Optional[int] = None,
        session_id: Optional[int] = None,
        rating: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatFeedback]:
        """
        Query feedback with filters.
        """
        conditions = [ChatFeedback.tenant_id == tenant_id]
        
        if message_id:
            conditions.append(ChatFeedback.message_id == message_id)
        if session_id:
            conditions.append(ChatFeedback.session_id == session_id)
        if rating is not None:
            conditions.append(ChatFeedback.rating == rating)
        if start_date:
            conditions.append(ChatFeedback.created_at >= start_date)
        if end_date:
            conditions.append(ChatFeedback.created_at <= end_date)
        
        result = await db.execute(
            select(ChatFeedback)
            .where(and_(*conditions))
            .order_by(ChatFeedback.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        return list(result.scalars().all())
    
    async def get_feedback_stats(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get feedback statistics for a tenant.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Count positive and negative
        result = await db.execute(
            select(
                ChatFeedback.rating,
                func.count(ChatFeedback.id).label('count')
            )
            .where(
                and_(
                    ChatFeedback.tenant_id == tenant_id,
                    ChatFeedback.created_at >= start_date
                )
            )
            .group_by(ChatFeedback.rating)
        )
        rating_counts = {row.rating: row.count for row in result.all()}
        
        positive = rating_counts.get(1, 0)
        negative = rating_counts.get(-1, 0)
        total = positive + negative
        
        # Issue type breakdown (for negative feedback)
        result = await db.execute(
            select(
                ChatFeedback.issue_type,
                func.count(ChatFeedback.id).label('count')
            )
            .where(
                and_(
                    ChatFeedback.tenant_id == tenant_id,
                    ChatFeedback.created_at >= start_date,
                    ChatFeedback.rating == -1,
                    ChatFeedback.issue_type.isnot(None)
                )
            )
            .group_by(ChatFeedback.issue_type)
        )
        issue_breakdown = {row.issue_type: row.count for row in result.all()}
        
        # Daily trend
        result = await db.execute(
            select(
                func.date(ChatFeedback.created_at).label('date'),
                ChatFeedback.rating,
                func.count(ChatFeedback.id).label('count')
            )
            .where(
                and_(
                    ChatFeedback.tenant_id == tenant_id,
                    ChatFeedback.created_at >= start_date
                )
            )
            .group_by(func.date(ChatFeedback.created_at), ChatFeedback.rating)
            .order_by(func.date(ChatFeedback.created_at))
        )
        
        daily_data = {}
        for row in result.all():
            date_str = str(row.date)
            if date_str not in daily_data:
                daily_data[date_str] = {'positive': 0, 'negative': 0}
            if row.rating == 1:
                daily_data[date_str]['positive'] = row.count
            else:
                daily_data[date_str]['negative'] = row.count
        
        return {
            'period_days': days,
            'total_feedback': total,
            'positive': positive,
            'negative': negative,
            'satisfaction_rate': round(positive / total * 100, 1) if total > 0 else 0,
            'issue_breakdown': issue_breakdown,
            'daily_trend': daily_data
        }
    
    async def get_negative_feedback_details(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get details of recent negative feedback for review.
        """
        feedback_list = await self.get_feedback(
            db, tenant_id, rating=-1, limit=limit
        )
        
        return [
            {
                'id': f.id,
                'message_id': f.message_id,
                'session_id': f.session_id,
                'issue_type': f.issue_type,
                'feedback_text': f.feedback_text,
                'created_at': f.created_at.isoformat()
            }
            for f in feedback_list
        ]
    
    async def get_quality_score(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 7
    ) -> float:
        """
        Calculate overall quality score based on recent feedback.
        Returns a score between 0 and 100.
        """
        stats = await self.get_feedback_stats(db, tenant_id, days)
        
        total = stats['total_feedback']
        if total == 0:
            return 75.0  # Default score when no feedback
        
        # Base score from satisfaction rate
        base_score = stats['satisfaction_rate']
        
        # Confidence adjustment based on sample size
        if total < 10:
            # Low confidence - move toward neutral
            confidence_factor = total / 10
            base_score = base_score * confidence_factor + 50 * (1 - confidence_factor)
        
        return round(base_score, 1)
