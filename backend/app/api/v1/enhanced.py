"""
Enhanced API endpoints for upgraded RAG functionality.
Includes: analytics, feedback, templates, streaming, quotas.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user, get_current_tenant_admin, verify_tenant_access
from app.models.user import User
from app.services.enhanced_rag_service import EnhancedRAGService
from app.services.feedback_service import FeedbackService
from app.services.quota_service import QuotaService
from app.services.template_service import TemplateService
from app.services.audit_service import AuditService
from app.services.cache_service import CacheService
from app.services.rate_limit_service import RateLimitService
from app.schemas.chat import ChatRequest, ChatResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v2", tags=["Enhanced"])


# ============== Schemas ==============

class FeedbackRequest(BaseModel):
    """Request to submit feedback on a response."""
    message_id: int
    session_id: int
    rating: int = Field(..., ge=-1, le=1, description="1 for 👍, -1 for 👎")
    feedback_text: Optional[str] = None
    issue_type: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    id: int
    message: str


class QuotaStatusResponse(BaseModel):
    """Current quota status for tenant."""
    documents: dict
    storage_mb: dict
    queries_today: dict
    tokens_today: dict
    resets_at: str


class TemplateResponse(BaseModel):
    """Chat template."""
    id: str
    name: str
    prompt_template: str
    description: Optional[str]
    category: str
    is_system: bool


class CreateTemplateRequest(BaseModel):
    """Request to create a custom template."""
    name: str
    prompt_template: str
    category: str = "custom"
    description: Optional[str] = None


class AnalyticsSummary(BaseModel):
    """Analytics summary for dashboard."""
    period_days: int
    total_queries: int
    unique_users: int
    avg_latency_ms: float
    cache_hit_rate: float
    satisfaction_rate: float
    top_queries: List[str]


class RateLimitStatus(BaseModel):
    """Rate limit status."""
    rpm_used: int
    rpm_limit: int
    rpm_remaining: int
    tpm_used: int
    tpm_limit: int
    tpm_remaining: int


# ============== Enhanced Chat ==============

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Enhanced chat with all modules"
)
async def enhanced_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced RAG pipeline with:
    - Hybrid search (semantic + keyword)
    - Result reranking
    - Confidence scoring
    - Context compression
    - Response caching
    - Rate limiting
    - Query suggestions
    """
    service = EnhancedRAGService(db)
    
    try:
        response = await service.chat(
            tenant_id=tenant_id,
            user_id=str(current_user.id),
            request=request
        )
        return response
    except Exception as e:
        logger.error(f"Enhanced chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your question"
        )


@router.post(
    "/chat/stream",
    summary="Stream chat response via SSE"
)
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream response tokens in real-time via Server-Sent Events.
    Provides better perceived latency for users.
    """
    # Note: Requires Groq client to be passed
    # This is a placeholder - actual implementation needs Groq client injection
    from app.services.stream_service import StreamService
    
    service = EnhancedRAGService(db)
    stream_svc = StreamService()
    
    return StreamingResponse(
        # service.stream_chat(tenant_id, str(current_user.id), request, groq_client),
        iter([stream_svc._format_sse({'type': 'info', 'message': 'Streaming requires Groq client configuration'})]),
        media_type="text/event-stream",
        headers=stream_svc.get_sse_headers()
    )


# ============== Feedback ==============

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit feedback on a response"
)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit 👍/👎 feedback on a chat response.
    Helps improve response quality over time.
    """
    service = FeedbackService()
    
    try:
        feedback = await service.submit_feedback(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            message_id=request.message_id,
            session_id=request.session_id,
            rating=request.rating,
            feedback_text=request.feedback_text,
            issue_type=request.issue_type
        )
        
        return FeedbackResponse(
            id=feedback.id,
            message="Feedback submitted successfully"
        )
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get(
    "/feedback/stats",
    summary="Get feedback statistics"
)
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """Get feedback statistics for the tenant."""
    service = FeedbackService()
    stats = await service.get_feedback_stats(db, tenant_id, days)
    
    return stats


class FeedbackListItem(BaseModel):
    """Feedback item for list response."""
    id: str
    message_id: int
    session_id: int
    user_id: str
    user_email: str
    user_name: Optional[str]
    rating: int
    feedback_text: Optional[str]
    issue_type: Optional[str]
    created_at: str


class FeedbackListResponse(BaseModel):
    """Response for feedback list."""
    feedback: List[FeedbackListItem]
    total: int
    page: int
    total_pages: int


@router.get(
    "/feedback/list",
    response_model=FeedbackListResponse,
    summary="List all feedback (admin only)"
)
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rating: Optional[int] = Query(None, ge=-1, le=1, description="Filter by rating"),
    current_user: User = Depends(get_current_tenant_admin),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    List all feedback for admin review.
    Allows filtering by rating type.
    """
    service = FeedbackService()
    
    offset = (page - 1) * page_size
    feedback_list = await service.get_feedback(
        db=db,
        tenant_id=tenant_id,
        rating=rating,
        limit=page_size,
        offset=offset
    )
    
    # Get total count for pagination
    from sqlalchemy import select, func
    from app.models.chat_feedback import ChatFeedback
    
    count_query = select(func.count(ChatFeedback.id)).where(
        ChatFeedback.tenant_id == tenant_id
    )
    if rating is not None:
        count_query = count_query.where(ChatFeedback.rating == rating)
    
    result = await db.execute(count_query)
    total = result.scalar() or 0
    total_pages = (total + page_size - 1) // page_size
    
    # Get user details
    from app.models.user import User as UserModel
    user_ids = list(set(str(f.user_id) for f in feedback_list))
    users_result = await db.execute(
        select(UserModel).where(UserModel.id.in_(user_ids))
    )
    users_map = {str(u.id): u for u in users_result.scalars().all()}
    
    items = []
    for f in feedback_list:
        user = users_map.get(str(f.user_id))
        items.append(FeedbackListItem(
            id=str(f.id),
            message_id=f.message_id if hasattr(f, 'message_id') else 0,
            session_id=f.session_id if hasattr(f, 'session_id') else 0,
            user_id=str(f.user_id),
            user_email=user.email if user else "Unknown",
            user_name=user.full_name if user else None,
            rating=f.rating,
            feedback_text=f.feedback_text,
            issue_type=f.issue_type,
            created_at=f.created_at.isoformat() if f.created_at else ""
        ))
    
    return FeedbackListResponse(
        feedback=items,
        total=total,
        page=page,
        total_pages=total_pages
    )


# ============== Quotas ==============

@router.get(
    "/quota",
    response_model=QuotaStatusResponse,
    summary="Get quota status"
)
async def get_quota_status(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current quota usage and limits.
    Shows documents, storage, queries, and token usage.
    """
    service = QuotaService()
    status = await service.get_quota_status(db, tenant_id)
    
    return QuotaStatusResponse(**status)


@router.get(
    "/rate-limit",
    response_model=RateLimitStatus,
    summary="Get rate limit status"
)
async def get_rate_limit_status(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access)
):
    """Get current rate limit status for API calls."""
    service = RateLimitService()
    status = await service.get_status(tenant_id)
    
    return RateLimitStatus(
        rpm_used=status['tenant']['rpm']['used'],
        rpm_limit=status['tenant']['rpm']['limit'],
        rpm_remaining=status['tenant']['rpm']['remaining'],
        tpm_used=status['tenant']['tpm']['used'],
        tpm_limit=status['tenant']['tpm']['limit'],
        tpm_remaining=status['tenant']['tpm']['remaining']
    )


# ============== Templates ==============

@router.get(
    "/templates",
    response_model=List[TemplateResponse],
    summary="Get available templates"
)
async def get_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available chat prompt templates.
    Templates help users form effective queries.
    """
    service = TemplateService()
    templates = await service.get_templates(db, tenant_id, category)
    
    return [TemplateResponse(**t) for t in templates]


@router.post(
    "/templates",
    response_model=TemplateResponse,
    summary="Create custom template"
)
async def create_template(
    request: CreateTemplateRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom prompt template for your organization."""
    service = TemplateService()
    template = await service.create_template(
        db=db,
        tenant_id=tenant_id,
        name=request.name,
        prompt_template=request.prompt_template,
        category=request.category,
        description=request.description
    )
    
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        prompt_template=template.prompt_template,
        description=template.description,
        category=template.category,
        is_system=False
    )


@router.delete(
    "/templates/{template_id}",
    summary="Delete custom template"
)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom template (system templates cannot be deleted)."""
    service = TemplateService()
    deleted = await service.delete_template(db, tenant_id, template_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be deleted"
        )
    
    return {"message": "Template deleted"}


# ============== Analytics ==============

@router.get(
    "/analytics/activity",
    summary="Get activity analytics"
)
async def get_activity_analytics(
    days: int = Query(7, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity analytics for the tenant.
    Includes queries, users, actions breakdown.
    """
    service = AuditService()
    summary = await service.get_tenant_activity_summary(db, tenant_id, days)
    
    return summary


@router.get(
    "/analytics/cache",
    summary="Get cache statistics"
)
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """Get cache hit/miss statistics."""
    service = CacheService()
    stats = await service.get_cache_stats(db, tenant_id)
    
    return stats


# ============== Audit Logs ==============

@router.get(
    "/audit-logs",
    summary="Get audit logs"
)
async def get_audit_logs(
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs for compliance and debugging.
    Filter by action type and date range.
    """
    service = AuditService()
    logs = await service.get_audit_logs(
        db=db,
        tenant_id=tenant_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return [
        {
            'id': log.id,
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'user_id': log.user_id,
            'details': log.details,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat()
        }
        for log in logs
    ]
