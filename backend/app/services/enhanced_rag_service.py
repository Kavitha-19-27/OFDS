"""
Enhanced RAG service with all 21 module upgrades.
Extends base RAG functionality with:
- Hybrid search (semantic + keyword)
- Reranking
- Confidence scoring
- Context compression
- Caching
- Rate limiting
- Streaming
- Source highlighting
- Query suggestions
"""
import time
import uuid
from typing import List, Optional, AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ValidationError
from app.models.chat_log import ChatLog
from app.repositories.document_repository import DocumentChunkRepository, DocumentRepository
from app.repositories.chat_repository import ChatRepository
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

# New services
from app.services.cache_service import CacheService
from app.services.hybrid_search_service import HybridSearchService
from app.services.reranker_service import RerankerService
from app.services.confidence_service import ConfidenceService
from app.services.compression_service import CompressionService
from app.services.rate_limit_service import RateLimitService, RateLimitExceededError
from app.services.stream_service import StreamService
from app.services.highlight_service import HighlightService
from app.services.suggestion_service import SuggestionService
from app.services.audit_service import AuditService
from app.services.quota_service import QuotaService, QuotaExceededError
from app.services.feedback_service import FeedbackService

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceChunk,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedRAGService:
    """
    Enhanced RAG service with all upgraded modules.
    Use this for the full-featured RAG pipeline.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunk_repo = DocumentChunkRepository(session)
        self.document_repo = DocumentRepository(session)
        self.chat_repo = ChatRepository(session)
        
        # Core services
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
        
        # Enhanced services
        self.cache_service = CacheService()
        self.hybrid_search_service = HybridSearchService()
        self.reranker_service = RerankerService()
        self.confidence_service = ConfidenceService()
        self.compression_service = CompressionService()
        self.rate_limit_service = RateLimitService()
        self.stream_service = StreamService()
        self.highlight_service = HighlightService()
        self.suggestion_service = SuggestionService()
        self.audit_service = AuditService()
        self.quota_service = QuotaService()
        self.feedback_service = FeedbackService()
        
        # Configuration
        self.enable_cache = True
        self.enable_hybrid_search = True
        self.enable_reranking = True
        self.enable_confidence = True
        self.enable_compression = True
    
    async def chat(
        self,
        tenant_id: str,
        user_id: str,
        request: ChatRequest,
        enable_streaming: bool = False
    ) -> ChatResponse:
        """
        Enhanced chat with all modules integrated.
        """
        start_time = time.time()
        session_id = request.session_id or str(uuid.uuid4())
        top_k = request.top_k or settings.top_k_retrieval
        
        tenant_id_int = int(tenant_id) if tenant_id.isdigit() else hash(tenant_id) % 1000000
        user_id_int = int(user_id) if user_id.isdigit() else hash(user_id) % 1000000
        
        logger.info(f"Enhanced RAG processing: tenant={tenant_id}, session={session_id}")
        
        # Check greetings
        if self._is_greeting(request.question):
            return await self._handle_greeting(tenant_id, user_id, session_id, request, start_time)
        
        # Step 1: Check cache
        if self.enable_cache:
            cached = await self.cache_service.get_cached_response(
                self.session, tenant_id_int, request.question
            )
            if cached:
                logger.info("Cache hit - returning cached response")
                return ChatResponse(
                    answer=cached['answer'],
                    question=request.question,
                    sources=cached.get('sources', []),
                    session_id=session_id,
                    model_used="cache",
                    tokens_used=0,
                    latency_ms=int((time.time() - start_time) * 1000)
                )
        
        # Step 2: Check quotas
        try:
            await self.quota_service.check_quota(self.session, tenant_id_int, 'queries')
        except QuotaExceededError as e:
            logger.warning(f"Quota exceeded for tenant {tenant_id}: {e}")
            return ChatResponse(
                answer="Daily query limit reached. Please try again tomorrow or upgrade your plan.",
                question=request.question,
                sources=[],
                session_id=session_id,
                model_used="quota-exceeded",
                tokens_used=0,
                latency_ms=int((time.time() - start_time) * 1000)
            )
        
        # Step 3: Check rate limits
        try:
            estimated_tokens = self.compression_service.estimate_tokens(request.question) + 500
            await self.rate_limit_service.acquire(tenant_id_int, estimated_tokens)
        except RateLimitExceededError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            return ChatResponse(
                answer=f"Rate limit reached. Please wait {e.retry_after:.0f} seconds and try again.",
                question=request.question,
                sources=[],
                session_id=session_id,
                model_used="rate-limited",
                tokens_used=0,
                latency_ms=int((time.time() - start_time) * 1000)
            )
        
        # Step 4: Generate query embedding
        query_embedding = await self.embedding_service.get_embedding(request.question)
        
        # Step 5: Search (hybrid or semantic-only)
        if self.enable_hybrid_search:
            search_results = await self._hybrid_search(
                tenant_id, query_embedding, request.question, top_k * 2
            )
        else:
            search_results = await self.vector_service.search(
                tenant_id=tenant_id,
                query_embedding=query_embedding,
                top_k=top_k * 2
            )
        
        if not search_results:
            return await self._no_documents_response(request.question, session_id, start_time, request.language_mode)
        
        # Step 6: Fetch chunks and prepare results
        chunk_ids = [chunk_id for chunk_id, _ in search_results]
        chunks = await self.chunk_repo.get_by_ids(chunk_ids, tenant_id)
        chunk_map = {c.id: c for c in chunks}
        
        retrieved_chunks = []
        for chunk_id, score in search_results:
            if chunk_id in chunk_map:
                chunk = chunk_map[chunk_id]
                doc = await self.document_repo.get_by_id(chunk.document_id)
                retrieved_chunks.append({
                    'chunk_id': chunk_id,
                    'content': chunk.content,
                    'score': score,
                    'document_id': chunk.document_id,
                    'document_name': doc.original_name if doc else "Unknown",
                    'page_number': chunk.page_number
                })
        
        # Step 7: Rerank
        if self.enable_reranking and len(retrieved_chunks) > top_k:
            retrieved_chunks = await self.reranker_service.rerank(
                request.question, retrieved_chunks, top_k
            )
        else:
            retrieved_chunks = retrieved_chunks[:top_k]
        
        # Step 8: Build context texts with source attribution
        context_texts = []
        for c in retrieved_chunks:
            page_info = f", Page {c['page_number']}" if c['page_number'] else ""
            context_with_source = f"(Source: {c['document_name']}{page_info})\n{c['content']}"
            context_texts.append(context_with_source)
        
        # Step 8b: Compress context if enabled
        if self.enable_compression:
            compressed_context, compression_stats = await self.compression_service.compress_context(
                request.question, retrieved_chunks
            )
            logger.debug(f"Compression: {compression_stats['ratio']:.0%} of original")
        else:
            compressed_context = "\n\n".join(context_texts)
        
        # Step 9: Generate response
        llm_response = await self.llm_service.generate_response(
            question=request.question,
            context_chunks=context_texts if not self.enable_compression else [compressed_context],
            language_mode=request.language_mode
        )
        answer = llm_response.answer
        
        # Step 10: Calculate confidence
        if self.enable_confidence:
            confidence = await self.confidence_service.calculate_confidence(
                request.question, retrieved_chunks, answer
            )
        else:
            confidence = {'confidence_level': 'unknown', 'confidence_score': 0}
        
        # Step 11: Generate suggestions
        suggestions = self.suggestion_service.generate_suggestions(
            request.question, answer, retrieved_chunks
        )
        
        # Step 12: Highlight sources
        highlight_result = self.highlight_service.highlight_sources(answer, retrieved_chunks)
        
        # Step 13: Build sources
        sources = []
        for c in retrieved_chunks:
            sources.append(SourceChunk(
                chunk_id=c['chunk_id'],
                document_id=c['document_id'],
                document_name=c['document_name'],
                content_preview=c['content'][:200] + "..." if len(c['content']) > 200 else c['content'],
                page_number=c['page_number'],
                relevance_score=round(c['score'], 4)
            ))
        
        # Calculate latency and tokens
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = llm_response.total_tokens
        
        # Step 14: Record usage
        await self.rate_limit_service.record(tenant_id_int, tokens_used)
        await self.quota_service.consume_quota(self.session, tenant_id_int, 'queries')
        await self.quota_service.consume_quota(self.session, tenant_id_int, 'tokens', tokens_used)
        
        # Step 15: Cache response
        if self.enable_cache:
            await self.cache_service.cache_response(
                self.session, tenant_id_int, request.question,
                {'answer': answer, 'sources': [s.model_dump() for s in sources]},
                [c['document_id'] for c in retrieved_chunks]
            )
        
        # Step 16: Log interaction
        await self.chat_repo.create(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            question=request.question,
            answer=answer,
            context_chunks=[{'chunk_id': c['chunk_id'], 'score': c['score']} for c in retrieved_chunks],
            model_used=llm_response.model,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
        
        # Step 17: Audit log
        await self.audit_service.log_action(
            self.session, tenant_id_int, user_id_int,
            AuditService.ACTION_CHAT_QUERY,
            resource_type='chat',
            details={
                'session_id': session_id,
                'confidence': confidence['confidence_level'],
                'sources_count': len(sources)
            }
        )
        
        logger.info(f"Enhanced RAG complete: latency={latency_ms}ms, confidence={confidence['confidence_level']}")
        
        # Build enhanced response
        response = ChatResponse(
            answer=answer,
            question=request.question,
            session_id=session_id,
            sources=sources,
            model_used=llm_response.model,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
        
        # Add enhanced fields to response dict
        response_dict = response.model_dump()
        response_dict['confidence'] = confidence
        response_dict['suggestions'] = suggestions
        response_dict['grounding_score'] = highlight_result['grounding_score']
        
        return response
    
    async def _hybrid_search(
        self,
        tenant_id: str,
        query_embedding: List[float],
        query_text: str,
        top_k: int
    ) -> List[tuple]:
        """Perform hybrid search combining semantic and keyword search."""
        # Semantic search
        semantic_results = await self.vector_service.search(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        # Get all chunks for BM25
        all_chunks = await self.chunk_repo.get_all_by_tenant(tenant_id, limit=10000)
        
        if not all_chunks:
            return semantic_results
        
        # Build BM25 documents
        documents = [
            {'chunk_id': c.id, 'content': c.content}
            for c in all_chunks
        ]
        
        # Perform hybrid search
        hybrid_results = await self.hybrid_search_service.hybrid_search(
            query_text=query_text,
            query_embedding=query_embedding,
            semantic_results=semantic_results,
            documents=documents,
            top_k=top_k
        )
        
        return hybrid_results
    
    def _is_greeting(self, text: str) -> bool:
        """Check if the text is a simple greeting."""
        greetings = [
            'hi', 'hello', 'hey', 'hii', 'hiii', 'good morning', 'good afternoon',
            'good evening', 'good night', 'howdy', 'sup', 'yo', 'greetings',
            'thanks', 'thank you', 'thx', 'bye', 'goodbye', 'see you', 'later',
            'ok', 'okay', 'yes', 'no', 'sure', 'hmm', 'hm', 'nice', 'cool', 'great'
        ]
        normalized = text.lower().strip().rstrip('!?.,:;')
        return normalized in greetings or len(normalized) < 4
    
    async def _handle_greeting(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        request: ChatRequest,
        start_time: float
    ) -> ChatResponse:
        """Handle greeting messages with language mode support."""
        normalized = request.question.lower().strip()
        language_mode = request.language_mode
        
        if language_mode == "tanglish":
            # Tanglish responses
            if any(g in normalized for g in ['hi', 'hello', 'hey', 'vanakkam', 'da', 'bro']):
                answer = """👋 **Vanakkam da! Document Intelligence ku Welcome!**

🤖 Naan unga Enterprise Document Analysis Assistant da! Naan help panna mudiyum:

📌 **Facts extract** pannuven unga documents la irundhu
📖 **Terms explain** pannuven document context la
🔬 **Analyze** pannuven document structure, purpose, themes
📝 **Summarize** pannuven document content
⚖️ **Compare** pannuven multiple documents
💡 **General questions** ku um answer pannuven

✨ Enna venum na kelu da - documents pathi or general topics - naan help pannren!"""
            elif any(g in normalized for g in ['thank', 'nandri']):
                answer = "😊 Paravala da! Innum doubts irundha kelu, naan irukken help panna! 💡"
            elif any(g in normalized for g in ['bye', 'goodbye', 'poi varren']):
                answer = "👋 Thanks da Document Intelligence use pannathuku! Eppo venum na thirumbi vaa. Take care! ✨"
            elif any(g in normalized for g in ['good morning', 'kaalaivananakkam']):
                answer = "🌅 Kaalaivananakkam da! Inniki enna help venum? 📄 Document analysis ah or 💡 general questions ah - rendu ku um ready!"
            elif any(g in normalized for g in ['good afternoon', 'mathiyavananakkam']):
                answer = "☀️ Mathiyavananakkam! Enna help pannanum da? 📄 Document analysis, 📖 explanations, or 💡 general questions - kelu!"
            elif any(g in normalized for g in ['good evening', 'good night', 'maalaivananakkam']):
                answer = "🌙 Maalaivananakkam da! Enna doubt irundhalum kelu. 📄 Documents or 💡 general topics - ready ah irukken!"
            else:
                answer = """🚀 **Document Intelligence Ready da!**

🤖 Naan unga AI assistant:
• 📄 Document analysis and fact extraction
• 📖 Term explanations and definitions
• 💡 General knowledge questions

✨ Enna help venum da inniki?"""
        else:
            # English responses
            if any(g in normalized for g in ['hi', 'hello', 'hey']):
                answer = """👋 **Welcome to Document Intelligence!**

🤖 I'm your Enterprise Document Analysis Assistant. I can help you:

📌 **Extract facts** from your uploaded documents
📖 **Explain terms** and their meaning within document context
🔬 **Analyze** document structure, purpose, and key themes
📝 **Summarize** document content
⚖️ **Compare** information across multiple documents
💡 **Answer general questions** when you need help

✨ Ask any question - about your documents or general topics - and I'll provide helpful, accurate responses!"""
            elif any(g in normalized for g in ['thank', 'nandri']):
                answer = "😊 You're welcome! If you have additional questions about your documents or anything else, feel free to ask. I'm here to help! 💡"
            elif any(g in normalized for g in ['bye', 'goodbye']):
                answer = "👋 Thank you for using Document Intelligence! Return anytime you need assistance. Have a great day! ✨"
            elif any(g in normalized for g in ['good morning']):
                answer = "🌅 Good morning! I'm ready to assist you today. What would you like help with? 📄 Document analysis or 💡 general questions - I'm here for both!"
            elif any(g in normalized for g in ['good afternoon']):
                answer = "☀️ Good afternoon! How can I assist you today? I can help with 📄 document analysis, 📖 explanations, or 💡 general questions!"
            elif any(g in normalized for g in ['good evening', 'good night']):
                answer = "🌙 Good evening! I'm here to help with any questions. What would you like to know? 📄 Documents or 💡 general topics - just ask!"
            else:
                answer = """🚀 **Document Intelligence Ready!**

🤖 I'm your AI assistant for:
• 📄 Document analysis and fact extraction
• 📖 Term explanations and definitions
• 💡 General knowledge questions

✨ What can I help you with today?"""
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        await self.chat_repo.create(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            question=request.question,
            answer=answer,
            context_chunks=[],
            model_used="greeting-handler",
            tokens_used=0,
            latency_ms=latency_ms
        )
        
        return ChatResponse(
            answer=answer,
            question=request.question,
            sources=[],
            session_id=session_id,
            model_used="greeting-handler",
            tokens_used=0,
            latency_ms=latency_ms
        )
    
    async def _no_documents_response(
        self,
        question: str,
        session_id: str,
        start_time: float,
        language_mode: str = "english"
    ) -> ChatResponse:
        """Generate response when no documents found - uses LLM for general knowledge."""
        # Call LLM with empty context for general knowledge response
        llm_response = await self.llm_service.generate_response(
            question=question,
            context_chunks=[],
            language_mode=language_mode
        )
        
        return ChatResponse(
            answer=llm_response.answer,
            question=question,
            sources=[],
            session_id=session_id,
            model_used=llm_response.model,
            tokens_used=llm_response.total_tokens,
            latency_ms=int((time.time() - start_time) * 1000)
        )
    
    async def stream_chat(
        self,
        tenant_id: str,
        user_id: str,
        request: ChatRequest,
        groq_client
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response via SSE.
        Use this for real-time token delivery.
        """
        # Similar pipeline but with streaming at the end
        query_embedding = await self.embedding_service.get_embedding(request.question)
        
        search_results = await self.vector_service.search(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=request.top_k or 4
        )
        
        if not search_results:
            error_msg = 'Documents illa da!' if request.language_mode == 'tanglish' else 'No documents found'
            yield self.stream_service._format_sse({
                'type': 'error',
                'error': error_msg
            })
            return
        
        # Fetch and prepare context
        chunk_ids = [cid for cid, _ in search_results]
        chunks = await self.chunk_repo.get_by_ids(chunk_ids, tenant_id)
        context_texts = [c.content for c in chunks]
        
        # Build messages
        context_str = "\n\n".join(context_texts)
        messages = [
            {"role": "system", "content": f"Answer based on this context:\n\n{context_str}"},
            {"role": "user", "content": request.question}
        ]
        
        # Stream response
        async for chunk in self.stream_service.stream_chat_response(
            groq_client, messages
        ):
            yield chunk
