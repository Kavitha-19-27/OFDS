"""
Schemas package initialization.
Export all Pydantic schemas.
"""
from app.schemas.auth import (
    TokenResponse,
    TokenPayload,
    LoginRequest,
    RefreshTokenRequest,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
)
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
)

__all__ = [
    # Auth
    "TokenResponse",
    "TokenPayload",
    "LoginRequest",
    "RefreshTokenRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    # Document
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentUploadResponse",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatHistoryResponse",
]
