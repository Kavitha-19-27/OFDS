"""
Models package initialization.
Export all models for easy importing.
"""
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.chat_log import ChatLog

# New models for 21-module upgrade
from app.models.document_access import DocumentAccess, AccessLevel
from app.models.audit_log import AuditLog
from app.models.tenant_quota import TenantQuota
from app.models.chat_feedback import ChatFeedback
from app.models.query_cache import QueryCache
from app.models.document_summary import DocumentSummary, SummaryType
from app.models.chat_template import ChatTemplate, DEFAULT_TEMPLATES
from app.models.retrieval_metrics import RetrievalMetrics, ConfidenceLevel
from app.models.ingestion_queue import IngestionQueue, QueueStatus
from app.models.retention_policy import RetentionPolicy, DEFAULT_RETENTION_POLICIES

__all__ = [
    # Core models
    "Tenant",
    "User",
    "UserRole",
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "ChatLog",
    # Enterprise models
    "DocumentAccess",
    "AccessLevel",
    "AuditLog",
    "TenantQuota",
    "RetentionPolicy",
    "DEFAULT_RETENTION_POLICIES",
    # Analytics models
    "ChatFeedback",
    "RetrievalMetrics",
    "ConfidenceLevel",
    # Performance models
    "QueryCache",
    "IngestionQueue",
    "QueueStatus",
    # UX models
    "DocumentSummary",
    "SummaryType",
    "ChatTemplate",
    "DEFAULT_TEMPLATES",
]
