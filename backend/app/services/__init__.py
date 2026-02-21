"""
Services package initialization.
"""
# Core services
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.tenant_service import TenantService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService

# Intelligence modules
from app.services.cache_service import CacheService
from app.services.hybrid_search_service import HybridSearchService, BM25Index
from app.services.reranker_service import RerankerService
from app.services.confidence_service import ConfidenceService, ConfidenceLevel
from app.services.compression_service import CompressionService
from app.services.summary_service import SummaryService

# Enterprise modules
from app.services.audit_service import AuditService
from app.services.quota_service import QuotaService, QuotaExceededError
from app.services.feedback_service import FeedbackService

# Performance modules
from app.services.stream_service import StreamService
from app.services.rate_limit_service import RateLimitService, RateLimiter, RateLimitExceededError

# UX modules
from app.services.template_service import TemplateService
from app.services.suggestion_service import SuggestionService
from app.services.highlight_service import HighlightService

__all__ = [
    # Core
    "AuthService",
    "UserService",
    "TenantService",
    "DocumentService",
    "EmbeddingService",
    "VectorService",
    "RAGService",
    "LLMService",
    # Intelligence
    "CacheService",
    "HybridSearchService",
    "BM25Index",
    "RerankerService",
    "ConfidenceService",
    "ConfidenceLevel",
    "CompressionService",
    "SummaryService",
    # Enterprise
    "AuditService",
    "QuotaService",
    "QuotaExceededError",
    "FeedbackService",
    # Performance
    "StreamService",
    "RateLimitService",
    "RateLimiter",
    "RateLimitExceededError",
    # UX
    "TemplateService",
    "SuggestionService",
    "HighlightService",
]
