"""
Trial/Guest upload endpoints - allows one free document upload without authentication.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.utils.logger import get_logger
from app.utils.validators import validate_file_extension, validate_file_size
from app.core.exceptions import ValidationError

logger = get_logger(__name__)
router = APIRouter(prefix="/trial", tags=["Trial"])

# In-memory storage for trial sessions (in production, use Redis)
trial_sessions: dict = {}

class TrialUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    session_id: str
    filename: str
    file_size: int
    expires_at: str


class TrialSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.document_id: Optional[str] = None
        self.filename: Optional[str] = None
        self.uploaded_at: Optional[datetime] = None
        self.expires_at: datetime = datetime.utcnow() + timedelta(hours=24)
        self.ip_address: Optional[str] = None


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_ip_limit(ip_address: str) -> bool:
    """Check if IP has already used trial upload."""
    for session in trial_sessions.values():
        if session.ip_address == ip_address and session.document_id:
            return False
    return True


@router.post(
    "/upload",
    response_model=TrialUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a trial document (no auth required)"
)
async def trial_upload(
    request: Request,
    file: UploadFile = File(..., description="Document file to upload"),
):
    """
    Upload a single document without authentication for trial purposes.
    
    Limitations:
    - One document per IP address
    - Max 10MB file size
    - Document expires after 24 hours
    - Supported formats: PDF, DOCX, TXT
    """
    client_ip = get_client_ip(request)
    
    # Check IP limit
    if not check_ip_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trial limit reached. Please create an account for unlimited uploads."
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Check file extension
    allowed_extensions = [".pdf", ".docx", ".doc", ".txt"]
    try:
        validate_file_extension(file.filename, allowed_extensions)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Read and validate file size
    content = await file.read()
    max_trial_size_mb = 10  # 10MB limit for trial
    
    try:
        validate_file_size(len(content), max_trial_size_mb)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create trial session
    session_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())
    
    trial_session = TrialSession(session_id)
    trial_session.document_id = document_id
    trial_session.filename = file.filename
    trial_session.uploaded_at = datetime.utcnow()
    trial_session.ip_address = client_ip
    
    # Store session
    trial_sessions[session_id] = trial_session
    
    logger.info(f"Trial document uploaded: {file.filename} from IP {client_ip}")
    
    # In a real implementation, you would:
    # 1. Store the file temporarily
    # 2. Process the document (extract text, chunk, embed)
    # 3. Allow limited queries against the document
    
    return TrialUploadResponse(
        success=True,
        message="Document uploaded successfully! Create an account to keep it permanently.",
        document_id=document_id,
        session_id=session_id,
        filename=file.filename,
        file_size=len(content),
        expires_at=trial_session.expires_at.isoformat()
    )


@router.get("/status/{session_id}")
async def get_trial_status(session_id: str):
    """Check status of a trial session."""
    session = trial_sessions.get(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial session not found or expired"
        )
    
    return {
        "session_id": session_id,
        "document_id": session.document_id,
        "filename": session.filename,
        "uploaded_at": session.uploaded_at.isoformat() if session.uploaded_at else None,
        "expires_at": session.expires_at.isoformat(),
        "is_expired": datetime.utcnow() > session.expires_at
    }


@router.delete("/session/{session_id}")
async def delete_trial_session(session_id: str):
    """Delete a trial session."""
    if session_id in trial_sessions:
        del trial_sessions[session_id]
        return {"message": "Trial session deleted"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Trial session not found"
    )


# Trial chat request/response models
class TrialChatRequest(BaseModel):
    session_id: str
    message: str


class TrialChatResponse(BaseModel):
    response: str
    prompts_used: int
    prompts_remaining: int
    session_id: str


# Track prompt counts per session (in production, use Redis)
trial_prompt_counts: dict = {}
MAX_TRIAL_PROMPTS = 10


@router.post(
    "/chat",
    response_model=TrialChatResponse,
    summary="Chat with trial document (limited to 10 prompts)"
)
async def trial_chat(request: TrialChatRequest):
    """
    Chat with a trial document.
    
    Limitations:
    - Maximum 10 prompts per trial session
    - Basic responses only
    - Session expires after 24 hours
    """
    # Allow demo sessions without upload
    is_demo = request.session_id.startswith("demo-")
    
    if is_demo:
        # Create demo session if it doesn't exist
        if request.session_id not in trial_sessions:
            demo_session = TrialSession(request.session_id)
            demo_session.filename = "Demo Document"
            demo_session.document_id = "demo-doc"
            demo_session.uploaded_at = datetime.utcnow()
            trial_sessions[request.session_id] = demo_session
        session = trial_sessions[request.session_id]
    else:
        session = trial_sessions.get(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trial session not found or expired. Please upload a document first."
            )
    
    # Check if session expired
    if datetime.utcnow() > session.expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Trial session has expired. Please create an account for unlimited access."
        )
    
    # Check prompt limit
    current_count = trial_prompt_counts.get(request.session_id, 0)
    if current_count >= MAX_TRIAL_PROMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trial prompt limit reached. Please create an account for unlimited access."
        )
    
    # Increment prompt count
    trial_prompt_counts[request.session_id] = current_count + 1
    
    # Generate a demo response (in production, this would call the actual RAG service)
    user_message = request.message.lower()
    filename = session.filename or "your document"
    
    # Simple response logic for demo
    if any(word in user_message for word in ['summary', 'summarize', 'overview']):
        response = f"""📄 **Document Summary: {filename}**

Based on my analysis of your uploaded document, here are the key highlights:

**Main Topic:** This document appears to cover important information relevant to your query.

**Key Sections:**
• Introduction and background context
• Main content and detailed explanations  
• Conclusions and recommendations

**Overall:** The document provides comprehensive information. For detailed analysis with all 6 AI modes (Summary, Key Points, Risk Analysis, Action Items, Q&A, Compare), create a free account!

✨ *This is a trial response. Full AI analysis available with a free account.*"""
    
    elif any(word in user_message for word in ['key points', 'important', 'highlights', 'main']):
        response = f"""🔑 **Key Points from {filename}:**

1. **Point 1:** Important information identified in the document
2. **Point 2:** Critical details and findings
3. **Point 3:** Notable sections requiring attention
4. **Point 4:** Relevant data and statistics
5. **Point 5:** Conclusions and next steps

💡 *Trial mode shows basic analysis. Unlock full Key Points extraction with a free account!*"""

    elif any(word in user_message for word in ['risk', 'danger', 'warning', 'concern']):
        response = f"""⚠️ **Risk Analysis for {filename}:**

**Potential Risks Identified:**
• Risk factors present in the document
• Areas requiring careful review
• Compliance considerations

**Risk Level:** Moderate (based on trial analysis)

🔒 *Full Risk Analysis mode available with a free account - includes detailed risk scoring and mitigation recommendations!*"""

    elif any(word in user_message for word in ['action', 'todo', 'task', 'next steps']):
        response = f"""✅ **Action Items from {filename}:**

1. [ ] Review the main findings
2. [ ] Follow up on key points
3. [ ] Address identified items
4. [ ] Schedule next review

📋 *Trial shows basic actions. Full Action Items extraction with priorities and deadlines available with a free account!*"""

    else:
        response = f"""🤖 **AI Response about {filename}:**

Thank you for your question: "{request.message}"

Based on my analysis of your document, I can provide relevant information and insights. The document contains valuable content that addresses your query.

**What I found:**
• Relevant sections that match your question
• Supporting details and context
• Related information throughout the document

📚 *This is a trial response. For comprehensive answers with source citations and confidence scores, create a free account!*

**Prompts remaining:** {MAX_TRIAL_PROMPTS - current_count - 1}"""

    logger.info(f"Trial chat: session={request.session_id}, prompt_count={current_count + 1}")
    
    return TrialChatResponse(
        response=response,
        prompts_used=current_count + 1,
        prompts_remaining=MAX_TRIAL_PROMPTS - current_count - 1,
        session_id=request.session_id
    )


# Cleanup expired sessions (would typically be a background task)
def cleanup_expired_sessions():
    """Remove expired trial sessions."""
    now = datetime.utcnow()
    expired = [sid for sid, session in trial_sessions.items() if now > session.expires_at]
    for sid in expired:
        del trial_sessions[sid]
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired trial sessions")
