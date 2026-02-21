"""
Document summarization service.
Generates various types of summaries for documents.
"""
from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import hashlib

from app.models.document_summary import DocumentSummary, SummaryType
from app.services.compression_service import CompressionService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SummaryService:
    """
    Service for generating document summaries.
    Supports multiple summary types with caching.
    """
    
    # Token limits per summary type (Groq optimized)
    SUMMARY_LIMITS = {
        SummaryType.BRIEF: 150,
        SummaryType.DETAILED: 400,
        SummaryType.KEYWORDS: 50,
        SummaryType.OUTLINE: 300
    }
    
    def __init__(self):
        self.compression_service = CompressionService()
    
    async def get_summary(
        self,
        db: AsyncSession,
        document_id: int,
        summary_type: SummaryType = SummaryType.BRIEF
    ) -> Optional[Dict]:
        """
        Get cached summary or generate new one.
        
        Args:
            db: Database session
            document_id: Document to summarize
            summary_type: Type of summary to generate
            
        Returns:
            Dict with summary content and metadata
        """
        # Check for cached summary
        result = await db.execute(
            select(DocumentSummary).where(
                DocumentSummary.document_id == document_id,
                DocumentSummary.summary_type == summary_type.value
            )
        )
        cached = result.scalar_one_or_none()
        
        if cached:
            logger.debug(f"Returning cached {summary_type.value} summary for doc {document_id}")
            return {
                'summary': cached.summary_content,
                'type': summary_type.value,
                'cached': True,
                'created_at': cached.created_at.isoformat()
            }
        
        return None
    
    async def store_summary(
        self,
        db: AsyncSession,
        document_id: int,
        summary_content: str,
        summary_type: SummaryType,
        model_used: str = "llama-3.3-70b-versatile"
    ) -> DocumentSummary:
        """Store a generated summary."""
        content_hash = hashlib.md5(summary_content.encode()).hexdigest()
        
        summary = DocumentSummary(
            document_id=document_id,
            summary_type=summary_type.value,
            summary_content=summary_content,
            content_hash=content_hash,
            model_used=model_used
        )
        
        db.add(summary)
        await db.commit()
        await db.refresh(summary)
        
        logger.info(f"Stored {summary_type.value} summary for doc {document_id}")
        return summary
    
    def get_summary_prompt(
        self,
        content: str,
        summary_type: SummaryType,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate the prompt for summarization.
        Compressed content is included.
        """
        # Get appropriate prompt based on summary type
        prompts = {
            SummaryType.BRIEF: (
                "Provide a brief summary of the following document in 2-3 sentences. "
                "Focus on the main topic and key takeaway.\n\n"
                f"Document:\n{content}\n\n"
                "Brief Summary:"
            ),
            SummaryType.DETAILED: (
                "Provide a detailed summary of the following document. "
                "Include main topics, key points, and important details. "
                "Use 3-5 paragraphs.\n\n"
                f"Document:\n{content}\n\n"
                "Detailed Summary:"
            ),
            SummaryType.KEYWORDS: (
                "Extract the 10 most important keywords or key phrases from this document. "
                "List them in order of importance.\n\n"
                f"Document:\n{content}\n\n"
                "Keywords:"
            ),
            SummaryType.OUTLINE: (
                "Create a structured outline of this document. "
                "Use hierarchical formatting with main topics and subtopics.\n\n"
                f"Document:\n{content}\n\n"
                "Outline:"
            )
        }
        
        return prompts.get(summary_type, prompts[SummaryType.BRIEF])
    
    async def prepare_content_for_summary(
        self,
        content: str,
        summary_type: SummaryType
    ) -> str:
        """
        Prepare and compress content for summary generation.
        """
        max_tokens = self.SUMMARY_LIMITS.get(summary_type, 150) * 3  # Input can be 3x output
        
        compressed = await self.compression_service.compress_for_summary(
            content,
            max_tokens=max_tokens
        )
        
        return compressed
    
    async def invalidate_summaries(
        self,
        db: AsyncSession,
        document_id: int
    ) -> int:
        """
        Invalidate all summaries for a document.
        Call this when document content changes.
        
        Returns:
            Number of summaries invalidated
        """
        result = await db.execute(
            select(DocumentSummary).where(
                DocumentSummary.document_id == document_id
            )
        )
        summaries = result.scalars().all()
        
        for summary in summaries:
            await db.delete(summary)
        
        await db.commit()
        
        logger.info(f"Invalidated {len(summaries)} summaries for doc {document_id}")
        return len(summaries)
    
    async def get_document_summaries(
        self,
        db: AsyncSession,
        document_id: int
    ) -> List[Dict]:
        """Get all cached summaries for a document."""
        result = await db.execute(
            select(DocumentSummary).where(
                DocumentSummary.document_id == document_id
            )
        )
        summaries = result.scalars().all()
        
        return [
            {
                'type': s.summary_type,
                'summary': s.summary_content,
                'model': s.model_used,
                'created_at': s.created_at.isoformat()
            }
            for s in summaries
        ]
    
    def estimate_summary_tokens(
        self,
        content_length: int,
        summary_type: SummaryType
    ) -> Dict[str, int]:
        """
        Estimate token usage for generating a summary.
        Useful for rate limit planning.
        """
        # Estimate input tokens (compressed content)
        input_tokens = min(
            content_length // 4,  # Approximate chars to tokens
            self.SUMMARY_LIMITS[summary_type] * 3  # Max input
        )
        
        # Expected output tokens
        output_tokens = self.SUMMARY_LIMITS[summary_type]
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        }
