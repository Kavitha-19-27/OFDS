"""
RAG service for orchestrating the retrieval-augmented generation pipeline.
Coordinates embedding, retrieval, and response generation.
"""
import time
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ValidationError
from app.models.chat_log import ChatLog
from app.repositories.document_repository import DocumentChunkRepository, DocumentRepository
from app.repositories.chat_repository import ChatRepository
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceChunk,
    ChatHistoryResponse,
    ChatHistoryItem,
    ChatSessionsListResponse,
    ChatSessionResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    Service for RAG (Retrieval-Augmented Generation) operations.
    Orchestrates the full pipeline from query to response.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunk_repo = DocumentChunkRepository(session)
        self.document_repo = DocumentRepository(session)
        self.chat_repo = ChatRepository(session)
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.llm_service = LLMService()
    
    def _is_greeting(self, text: str) -> bool:
        """Check if the text is a simple greeting or conversational message."""
        greetings = [
            'hi', 'hello', 'hey', 'hii', 'hiii', 'good morning', 'good afternoon', 
            'good evening', 'good night', 'howdy', 'sup', 'yo', 'greetings',
            'thanks', 'thank you', 'thx', 'bye', 'goodbye', 'see you', 'later',
            'ok', 'okay', 'yes', 'no', 'sure', 'hmm', 'hm', 'nice', 'cool', 'great'
        ]
        normalized = text.lower().strip().rstrip('!?.,:;')
        return normalized in greetings or len(normalized) < 4
    
    def _get_greeting_response(self, text: str, language_mode: str = "english") -> str:
        """Get an appropriate response for greetings based on language mode."""
        normalized = text.lower().strip()
        
        if language_mode == "tanglish":
            # Tanglish responses
            if any(g in normalized for g in ['hi', 'hello', 'hey', 'howdy', 'yo', 'greetings', 'vanakkam', 'da', 'bro']):
                return """👋 **Vanakkam da! Document Intelligence ku Welcome!**

🤖 Naan unga Enterprise Document Analysis Assistant da! Naan help panna mudiyum:

📌 **Facts extract** pannuven unga documents la irundhu
📖 **Terms explain** pannuven document context la
🔬 **Analyze** pannuven document structure, purpose, themes
📝 **Summarize** pannuven document content
⚖️ **Compare** pannuven multiple documents
💡 **General questions** ku um answer pannuven

✨ Enna venum na kelu da - documents pathi or general topics - naan help pannren!"""
            elif any(g in normalized for g in ['thank', 'thx', 'nandri']):
                return "😊 Paravala da! Innum doubts irundha kelu, naan irukken help panna! 💡"
            elif any(g in normalized for g in ['bye', 'goodbye', 'see you', 'later', 'poi varren']):
                return "👋 Thanks da Document Intelligence use pannathuku! Eppo venum na thirumbi vaa. Take care! ✨"
            elif any(g in normalized for g in ['good morning', 'kaalaivananakkam']):
                return "🌅 Kaalaivananakkam da! Inniki enna help venum? 📄 Document analysis ah or 💡 general questions ah - rendu ku um ready!"
            elif any(g in normalized for g in ['good afternoon', 'mathiyavananakkam']):
                return "☀️ Mathiyavananakkam! Enna help pannanum da? 📄 Document analysis, 📖 explanations, or 💡 general questions - kelu!"
            elif any(g in normalized for g in ['good evening', 'good night', 'maalaivananakkam']):
                return "🌙 Maalaivananakkam da! Enna doubt irundhalum kelu. 📄 Documents or 💡 general topics - ready ah irukken!"
            else:
                return """🚀 **Document Intelligence Ready da!**

🤖 Naan unga AI assistant:
• 📄 Document analysis and fact extraction
• 📖 Term explanations and definitions
• 💡 General knowledge questions

✨ Enna help venum da inniki?"""
        else:
            # English responses
            if any(g in normalized for g in ['hi', 'hello', 'hey', 'howdy', 'yo', 'greetings']):
                return """👋 **Welcome to Document Intelligence!**

🤖 I'm your Enterprise Document Analysis Assistant. I can help you:

📌 **Extract facts** from your uploaded documents
📖 **Explain terms** and their meaning within document context
🔬 **Analyze** document structure, purpose, and key themes
📝 **Summarize** document content
⚖️ **Compare** information across multiple documents
💡 **Answer general questions** when you need help

✨ Ask any question - about your documents or general topics - and I'll provide helpful, accurate responses!"""
            elif any(g in normalized for g in ['thank', 'thx']):
                return "😊 You're welcome! If you have additional questions about your documents or anything else, feel free to ask. I'm here to help! 💡"
            elif any(g in normalized for g in ['bye', 'goodbye', 'see you', 'later']):
                return "👋 Thank you for using Document Intelligence! Return anytime you need assistance. Have a great day! ✨"
            elif any(g in normalized for g in ['good morning']):
                return "🌅 Good morning! I'm ready to assist you today. What would you like help with? 📄 Document analysis or 💡 general questions - I'm here for both!"
            elif any(g in normalized for g in ['good afternoon']):
                return "☀️ Good afternoon! How can I assist you today? I can help with 📄 document analysis, 📖 explanations, or 💡 general questions!"
            elif any(g in normalized for g in ['good evening', 'good night']):
                return "🌙 Good evening! I'm here to help with any questions. What would you like to know? 📄 Documents or 💡 general topics - just ask!"
            else:
                return """🚀 **Document Intelligence Ready!**

🤖 I'm your AI assistant for:
• 📄 Document analysis and fact extraction
• 📖 Term explanations and definitions
• 💡 General knowledge questions

✨ What can I help you with today?"""
    
    async def chat(
        self,
        tenant_id: str,
        user_id: str,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Process a chat request through the RAG pipeline.
        
        Pipeline:
        1. Generate query embedding
        2. Retrieve top-k similar chunks
        3. Fetch chunk content from database
        4. Generate response using LLM
        5. Log the interaction
        
        Args:
            tenant_id: Tenant ID for index selection
            user_id: User ID for logging
            request: Chat request with question
            
        Returns:
            ChatResponse with answer and sources
        """
        start_time = time.time()
        
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        top_k = request.top_k or settings.top_k_retrieval
        
        logger.info(
            "Processing chat request",
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            question_length=len(request.question)
        )
        
        # Check if it's a simple greeting - respond without RAG
        if self._is_greeting(request.question):
            answer = self._get_greeting_response(request.question, request.language_mode)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log the greeting interaction
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
        
        # Step 1: Generate query embedding
        query_embedding = await self.embedding_service.get_embedding(request.question)
        
        # Step 2: Search vector index
        search_results = await self.vector_service.search(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        if not search_results:
            # No relevant chunks found - still call LLM for general knowledge response
            context_texts = []
            sources = []
            context_chunks = []
            
            # Generate response using LLM (will use general knowledge mode)
            llm_response = await self.llm_service.generate_response(
                question=request.question,
                context_chunks=context_texts,
                language_mode=request.language_mode
            )
            answer = llm_response.answer
        else:
            # Step 3: Fetch chunk content
            chunk_ids = [chunk_id for chunk_id, _ in search_results]
            chunks = await self.chunk_repo.get_by_ids(chunk_ids, tenant_id)
            
            # Create a mapping for quick lookup
            chunk_map = {c.id: c for c in chunks}
            
            # Prepare context and sources
            context_texts = []
            sources = []
            context_chunks = []
            
            for chunk_id, score in search_results:
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id]
                    
                    # Get document info
                    document = await self.document_repo.get_by_id(chunk.document_id)
                    doc_name = document.original_name if document else "Unknown Document"
                    
                    # Build context with source attribution for better LLM context
                    page_info = f", Page {chunk.page_number}" if chunk.page_number else ""
                    context_with_source = f"(Source: {doc_name}{page_info})\n{chunk.content}"
                    context_texts.append(context_with_source)
                    
                    sources.append(SourceChunk(
                        chunk_id=chunk_id,
                        document_id=chunk.document_id,
                        document_name=doc_name,
                        content_preview=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        page_number=chunk.page_number,
                        relevance_score=round(score, 4)
                    ))
                    
                    context_chunks.append({
                        "chunk_id": chunk_id,
                        "score": score
                    })
            
            # Step 4: Generate response
            llm_response = await self.llm_service.generate_response(
                question=request.question,
                context_chunks=context_texts,
                language_mode=request.language_mode
            )
            answer = llm_response.answer
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Step 5: Log the interaction
        tokens_used = llm_response.total_tokens if 'llm_response' in dir() else 0
        model_used = llm_response.model if 'llm_response' in dir() else settings.openai_chat_model
        
        await self.chat_repo.create(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            question=request.question,
            answer=answer,
            context_chunks=context_chunks if context_chunks else None,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
        
        logger.info(
            "Chat response generated",
            tenant_id=tenant_id,
            session_id=session_id,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            sources=len(sources)
        )
        
        return ChatResponse(
            answer=answer,
            question=request.question,
            session_id=session_id,
            sources=sources,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
    
    async def get_chat_history(
        self,
        tenant_id: str,
        user_id: str,
        session_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ChatHistoryResponse:
        """
        Get chat history for a user.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            session_id: Optional session ID to filter by
            page: Page number
            page_size: Items per page
            
        Returns:
            ChatHistoryResponse with paginated history
        """
        skip = (page - 1) * page_size
        
        if session_id:
            logs = await self.chat_repo.get_by_session(
                session_id=session_id,
                tenant_id=tenant_id,
                skip=skip,
                limit=page_size
            )
        else:
            logs = await self.chat_repo.get_user_history(
                user_id=user_id,
                tenant_id=tenant_id,
                skip=skip,
                limit=page_size
            )
        
        total = await self.chat_repo.count_by_tenant(tenant_id)
        pages = (total + page_size - 1) // page_size
        
        history = [
            ChatHistoryItem(
                id=log.id,
                question=log.question,
                answer=log.answer,
                session_id=log.session_id,
                created_at=log.created_at,
                sources=None  # Could reconstruct from context_chunks if needed
            )
            for log in logs
        ]
        
        return ChatHistoryResponse(
            history=history,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    
    async def get_user_sessions(
        self,
        tenant_id: str,
        user_id: str
    ) -> ChatSessionsListResponse:
        """
        Get list of chat sessions for a user.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            List of chat sessions
        """
        sessions_data = await self.chat_repo.get_user_sessions(user_id, tenant_id)
        
        sessions = [
            ChatSessionResponse(
                session_id=s["session_id"],
                message_count=s["message_count"],
                first_message=s["first_message"],
                last_message=s["last_message"]
            )
            for s in sessions_data
        ]
        
        return ChatSessionsListResponse(
            sessions=sessions,
            total=len(sessions)
        )
    
    async def delete_session(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str
    ) -> int:
        """
        Delete all messages in a chat session.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            session_id: Session ID to delete
            
        Returns:
            Number of deleted messages
        """
        logs = await self.chat_repo.get_by_session(
            session_id=session_id,
            tenant_id=tenant_id,
            limit=1000
        )
        
        count = 0
        for log in logs:
            if log.user_id == user_id:
                await self.chat_repo.delete(log)
                count += 1
        
        logger.info(
            "Chat session deleted",
            session_id=session_id,
            messages_deleted=count
        )
        
        return count
