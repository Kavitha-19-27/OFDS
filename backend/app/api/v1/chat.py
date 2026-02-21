"""
Chat endpoints for RAG-based question answering.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, verify_tenant_access
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatSessionsListResponse,
)
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question"
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question and get an AI-generated answer based on your documents.
    
    The RAG pipeline:
    1. Embeds your question using OpenAI
    2. Searches for relevant document chunks
    3. Uses context to generate an accurate answer
    4. Returns answer with source citations
    
    Use `session_id` to maintain conversation context across multiple questions.
    """
    rag_service = RAGService(db)
    
    try:
        response = await rag_service.chat(
            tenant_id=tenant_id,
            user_id=current_user.id,
            request=request
        )
        
        return response
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(
            "Chat failed",
            error=str(e),
            user_id=current_user.id,
            tenant_id=tenant_id
        )
        
        # Check for API key related errors
        if "api_key" in error_msg or "invalid_api_key" in error_msg or "incorrect api key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key is not configured. Please set a valid OPENAI_API_KEY in the server configuration."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your question. Please try again."
        )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Get chat history"
)
async def get_chat_history(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history for the current user.
    
    Can be filtered by session_id to get messages from a specific conversation.
    Results are paginated.
    """
    rag_service = RAGService(db)
    
    history = await rag_service.get_chat_history(
        tenant_id=tenant_id,
        user_id=current_user.id,
        session_id=session_id,
        page=page,
        page_size=page_size
    )
    
    return history


@router.get(
    "/sessions",
    response_model=ChatSessionsListResponse,
    summary="Get chat sessions"
)
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all chat sessions for the current user.
    
    Each session represents a conversation thread.
    """
    rag_service = RAGService(db)
    
    sessions = await rag_service.get_user_sessions(
        tenant_id=tenant_id,
        user_id=current_user.id
    )
    
    return sessions


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chat session"
)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(verify_tenant_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat session and all its messages.
    
    This action is irreversible.
    """
    rag_service = RAGService(db)
    
    deleted_count = await rag_service.delete_session(
        tenant_id=tenant_id,
        user_id=current_user.id,
        session_id=session_id
    )
    
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or no messages to delete"
        )
    
    logger.info(
        "Chat session deleted",
        session_id=session_id,
        user_id=current_user.id,
        messages_deleted=deleted_count
    )
