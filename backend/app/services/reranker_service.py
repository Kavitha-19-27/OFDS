"""
Reranker service for improving search result quality.
Uses lightweight scoring to re-rank initial retrieval results.
"""
from typing import List, Dict, Tuple, Optional
import re
from collections import Counter

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RerankerService:
    """
    Service for reranking search results.
    Uses multiple lightweight signals without external API calls.
    """
    
    def __init__(self):
        # Optional: cross-encoder model (lazy loaded)
        self._cross_encoder = None
        self._use_cross_encoder = False
    
    def _try_load_cross_encoder(self) -> bool:
        """Try to load cross-encoder model if available."""
        try:
            from sentence_transformers import CrossEncoder
            self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            self._use_cross_encoder = True
            logger.info("Cross-encoder loaded for reranking")
            return True
        except Exception as e:
            logger.debug(f"Cross-encoder not available: {e}")
            self._use_cross_encoder = False
            return False
    
    async def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int = 4
    ) -> List[Dict]:
        """
        Rerank search results for better relevance.
        
        Args:
            query: Original query
            results: List of result dicts with 'chunk_id', 'content', 'score'
            top_k: Number of results to return
            
        Returns:
            Reranked list of results with updated scores
        """
        if not results:
            return []
        
        # Try cross-encoder first (best quality)
        if self._use_cross_encoder or self._try_load_cross_encoder():
            return await self._rerank_with_cross_encoder(query, results, top_k)
        
        # Fall back to lightweight reranking
        return self._rerank_lightweight(query, results, top_k)
    
    async def _rerank_with_cross_encoder(
        self,
        query: str,
        results: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """Rerank using cross-encoder model."""
        try:
            pairs = [(query, r['content']) for r in results]
            scores = self._cross_encoder.predict(pairs)
            
            # Add cross-encoder scores
            for result, ce_score in zip(results, scores):
                result['original_score'] = result.get('score', 0)
                result['rerank_score'] = float(ce_score)
                # Combine scores
                result['score'] = 0.3 * result['original_score'] + 0.7 * float(ce_score)
            
            # Sort by combined score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.debug(f"Reranked with cross-encoder, top score: {results[0]['score']:.4f}")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            return self._rerank_lightweight(query, results, top_k)
    
    def _rerank_lightweight(
        self,
        query: str,
        results: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """
        Lightweight reranking using multiple signals.
        No external API calls required.
        """
        query_tokens = set(self._tokenize(query.lower()))
        
        for result in results:
            content = result.get('content', '')
            original_score = result.get('score', 0)
            
            # Calculate multiple scoring signals
            signals = {
                'exact_match': self._exact_match_score(query, content),
                'keyword_coverage': self._keyword_coverage_score(query_tokens, content),
                'query_terms_density': self._query_term_density(query_tokens, content),
                'position_boost': self._position_boost(query_tokens, content),
                'length_penalty': self._length_penalty(content)
            }
            
            # Weighted combination
            rerank_score = (
                0.25 * signals['exact_match'] +
                0.25 * signals['keyword_coverage'] +
                0.20 * signals['query_terms_density'] +
                0.15 * signals['position_boost'] +
                0.15 * signals['length_penalty']
            )
            
            # Combine with original semantic score
            result['original_score'] = original_score
            result['rerank_score'] = rerank_score
            result['score'] = 0.6 * original_score + 0.4 * rerank_score
            result['rerank_signals'] = signals
        
        # Sort by combined score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.debug(f"Lightweight reranking complete, top score: {results[0]['score']:.4f}")
        return results[:top_k]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for analysis."""
        return re.findall(r'\b\w+\b', text.lower())
    
    def _exact_match_score(self, query: str, content: str) -> float:
        """Score based on exact phrase matches."""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Full query match
        if query_lower in content_lower:
            return 1.0
        
        # Check for significant n-gram matches
        query_words = query_lower.split()
        max_ngram_match = 0
        
        for n in range(len(query_words), 1, -1):
            for i in range(len(query_words) - n + 1):
                ngram = ' '.join(query_words[i:i+n])
                if ngram in content_lower:
                    max_ngram_match = max(max_ngram_match, n / len(query_words))
                    break
        
        return max_ngram_match
    
    def _keyword_coverage_score(self, query_tokens: set, content: str) -> float:
        """Score based on how many query keywords appear in content."""
        if not query_tokens:
            return 0.0
        
        content_tokens = set(self._tokenize(content.lower()))
        matches = query_tokens.intersection(content_tokens)
        
        return len(matches) / len(query_tokens)
    
    def _query_term_density(self, query_tokens: set, content: str) -> float:
        """Score based on density of query terms in content."""
        if not query_tokens:
            return 0.0
        
        content_tokens = self._tokenize(content.lower())
        if not content_tokens:
            return 0.0
        
        query_term_count = sum(1 for t in content_tokens if t in query_tokens)
        density = query_term_count / len(content_tokens)
        
        # Normalize to reasonable range
        return min(1.0, density * 10)
    
    def _position_boost(self, query_tokens: set, content: str) -> float:
        """Boost score if query terms appear early in content."""
        content_tokens = self._tokenize(content.lower())
        if not content_tokens or not query_tokens:
            return 0.0
        
        # Find first occurrence of any query term
        for i, token in enumerate(content_tokens[:50]):  # Check first 50 tokens
            if token in query_tokens:
                # Earlier = higher score
                return 1.0 - (i / 50)
        
        return 0.0
    
    def _length_penalty(self, content: str) -> float:
        """
        Slight penalty for very short or very long content.
        Prefer medium-length chunks.
        """
        length = len(content)
        
        # Ideal range: 200-1000 characters
        if 200 <= length <= 1000:
            return 1.0
        elif length < 200:
            return length / 200
        else:
            return max(0.5, 1000 / length)
