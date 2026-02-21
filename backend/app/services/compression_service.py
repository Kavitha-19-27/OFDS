"""
Context compression service for optimizing LLM token usage.
Critical for Groq free tier limits (6000 TPM).
"""
from typing import List, Dict, Tuple, Optional
import re
from collections import Counter

from app.utils.logger import get_logger

logger = get_logger(__name__)


class CompressionService:
    """
    Service for compressing retrieved context before LLM calls.
    Reduces token usage while preserving relevance.
    """
    
    # Default limits optimized for Groq free tier
    DEFAULT_MAX_TOKENS = 2000  # Leave room for system prompt and response
    CHARS_PER_TOKEN = 4  # Approximate for English text
    
    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * self.CHARS_PER_TOKEN
    
    async def compress_context(
        self,
        query: str,
        chunks: List[Dict],
        max_tokens: Optional[int] = None
    ) -> Tuple[str, Dict]:
        """
        Compress retrieved chunks to fit within token budget.
        
        Args:
            query: Original user query
            chunks: List of chunks with 'content' and 'score'
            max_tokens: Override max tokens limit
            
        Returns:
            Tuple of (compressed_context, compression_stats)
        """
        if not chunks:
            return "", {'original_tokens': 0, 'compressed_tokens': 0, 'ratio': 1.0}
        
        max_chars = (max_tokens or self.max_tokens) * self.CHARS_PER_TOKEN
        
        # Calculate original size
        original_text = '\n\n'.join(c.get('content', '') for c in chunks)
        original_tokens = len(original_text) // self.CHARS_PER_TOKEN
        
        # If already within budget, return as-is
        if len(original_text) <= max_chars:
            return original_text, {
                'original_tokens': original_tokens,
                'compressed_tokens': original_tokens,
                'ratio': 1.0,
                'method': 'none'
            }
        
        # Apply compression pipeline
        compressed, method = await self._compress_pipeline(
            query, chunks, max_chars
        )
        
        compressed_tokens = len(compressed) // self.CHARS_PER_TOKEN
        
        return compressed, {
            'original_tokens': original_tokens,
            'compressed_tokens': compressed_tokens,
            'ratio': round(compressed_tokens / original_tokens, 2) if original_tokens > 0 else 0,
            'method': method
        }
    
    async def _compress_pipeline(
        self,
        query: str,
        chunks: List[Dict],
        max_chars: int
    ) -> Tuple[str, str]:
        """
        Multi-stage compression pipeline.
        Progressively applies more aggressive compression as needed.
        """
        query_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))
        
        # Stage 1: Extract most relevant sentences from each chunk
        relevant_sentences = []
        for chunk in chunks:
            content = chunk.get('content', '')
            score = chunk.get('score', 0)
            sentences = self._extract_sentences(content)
            
            for sentence in sentences:
                relevance = self._sentence_relevance(sentence, query_terms)
                relevant_sentences.append({
                    'text': sentence,
                    'relevance': relevance,
                    'chunk_score': score,
                    'combined': relevance * 0.6 + score * 0.4
                })
        
        # Sort by combined relevance
        relevant_sentences.sort(key=lambda x: x['combined'], reverse=True)
        
        # Stage 2: Select sentences within budget
        selected = []
        current_chars = 0
        
        for sent in relevant_sentences:
            sent_len = len(sent['text'])
            if current_chars + sent_len + 2 <= max_chars:  # +2 for separator
                selected.append(sent['text'])
                current_chars += sent_len + 2
        
        if selected:
            compressed_text = ' '.join(selected)
            if len(compressed_text) <= max_chars:
                return compressed_text, 'sentence_extraction'
        
        # Stage 3: If still too large, apply abstractive compression
        # (For now, use truncation with smart boundaries)
        return self._smart_truncate(selected, max_chars), 'smart_truncation'
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out very short or empty sentences
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _sentence_relevance(self, sentence: str, query_terms: set) -> float:
        """
        Calculate sentence relevance to query.
        Returns score between 0 and 1.
        """
        if not query_terms:
            return 0.5
        
        sentence_terms = set(re.findall(r'\b\w{3,}\b', sentence.lower()))
        if not sentence_terms:
            return 0.0
        
        # Term overlap
        overlap = len(query_terms.intersection(sentence_terms))
        coverage = overlap / len(query_terms)
        
        # Density bonus (query terms per sentence length)
        density = overlap / len(sentence_terms) if sentence_terms else 0
        
        # Position bonus for sentences with query terms early
        first_match = len(sentence)
        for term in query_terms:
            pos = sentence.lower().find(term)
            if pos >= 0:
                first_match = min(first_match, pos)
        position_score = 1 - (first_match / len(sentence)) if sentence else 0
        
        return (coverage * 0.5 + density * 0.3 + position_score * 0.2)
    
    def _smart_truncate(self, sentences: List[str], max_chars: int) -> str:
        """
        Smart truncation that preserves complete sentences.
        """
        if not sentences:
            return ""
        
        result = []
        current_chars = 0
        
        for sent in sentences:
            if current_chars + len(sent) + 1 <= max_chars:
                result.append(sent)
                current_chars += len(sent) + 1
            else:
                # Truncate last sentence if needed
                remaining = max_chars - current_chars
                if remaining > 50:  # Only add if meaningful
                    truncated = sent[:remaining-3] + "..."
                    result.append(truncated)
                break
        
        return ' '.join(result)
    
    async def compress_for_summary(
        self,
        text: str,
        max_tokens: int = 1000
    ) -> str:
        """
        Compress text specifically for summarization.
        Preserves key information and structure.
        """
        max_chars = max_tokens * self.CHARS_PER_TOKEN
        
        if len(text) <= max_chars:
            return text
        
        # Extract key sentences based on position and content
        sentences = self._extract_sentences(text)
        
        # Score sentences based on:
        # 1. Position (first/last sentences of paragraphs are important)
        # 2. Contains numbers/statistics
        # 3. Contains key phrases
        
        scored_sentences = []
        for i, sent in enumerate(sentences):
            score = 0.5  # Base score
            
            # Position bonus (first and last sentences)
            if i < 3:
                score += 0.2 * (3 - i) / 3
            if i >= len(sentences) - 2:
                score += 0.1
            
            # Contains numbers (likely important facts)
            if re.search(r'\d+', sent):
                score += 0.15
            
            # Contains key phrases
            key_phrases = ['important', 'key', 'main', 'critical', 'essential', 
                          'conclusion', 'result', 'summary', 'therefore', 'however']
            for phrase in key_phrases:
                if phrase in sent.lower():
                    score += 0.1
                    break
            
            scored_sentences.append((score, sent))
        
        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        selected = []
        current_chars = 0
        
        for score, sent in scored_sentences:
            if current_chars + len(sent) + 2 <= max_chars:
                selected.append(sent)
                current_chars += len(sent) + 2
        
        return ' '.join(selected)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // self.CHARS_PER_TOKEN + 1
    
    def get_token_budget(self, current_usage: int, max_total: int = 5000) -> int:
        """
        Calculate remaining token budget.
        Useful for managing Groq rate limits.
        """
        remaining = max_total - current_usage
        return max(0, remaining)
