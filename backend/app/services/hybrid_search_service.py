"""
Hybrid Search service combining semantic and keyword search.
Uses Reciprocal Rank Fusion (RRF) for score combination.
"""
import math
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np
from rank_bm25 import BM25Okapi
import re

from app.utils.logger import get_logger

logger = get_logger(__name__)


class BM25Index:
    """
    BM25 index for keyword-based search.
    Lightweight and runs locally (no API calls).
    """
    
    def __init__(self):
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.bm25: Optional[BM25Okapi] = None
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        # Remove very short tokens and stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                     'from', 'as', 'or', 'and', 'but', 'if', 'so', 'yet', 'both',
                     'this', 'that', 'these', 'those', 'it', 'its'}
        return [t for t in tokens if len(t) > 2 and t not in stopwords]
    
    def build(self, documents: List[str], doc_ids: List[str]) -> None:
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of document texts
            doc_ids: Corresponding document/chunk IDs
        """
        self.documents = documents
        self.doc_ids = doc_ids
        
        tokenized = [self.tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        
        logger.info(f"BM25 index built with {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search using BM25.
        
        Returns:
            List of (doc_id, score) tuples
        """
        if not self.bm25:
            return []
        
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []
        
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.doc_ids[idx], float(scores[idx])))
        
        return results
    
    def add_document(self, doc_id: str, text: str) -> None:
        """Add a single document and rebuild index."""
        self.documents.append(text)
        self.doc_ids.append(doc_id)
        tokenized = [self.tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)


class HybridSearchService:
    """
    Service for hybrid search combining semantic and keyword search.
    Uses Reciprocal Rank Fusion (RRF) for final ranking.
    """
    
    # Score fusion parameter (standard RRF constant)
    RRF_K = 60
    
    # Weight for semantic vs keyword search
    SEMANTIC_WEIGHT = 0.7
    KEYWORD_WEIGHT = 0.3
    
    def __init__(self):
        # Per-tenant BM25 indexes (lazy loaded)
        self._bm25_indexes: Dict[str, BM25Index] = {}
    
    def get_or_create_bm25_index(self, tenant_id: str) -> BM25Index:
        """Get or create BM25 index for tenant."""
        if tenant_id not in self._bm25_indexes:
            self._bm25_indexes[tenant_id] = BM25Index()
        return self._bm25_indexes[tenant_id]
    
    def build_bm25_index(
        self,
        tenant_id: str,
        chunks: List[Dict[str, str]]
    ) -> None:
        """
        Build BM25 index for a tenant's documents.
        
        Args:
            tenant_id: Tenant ID
            chunks: List of dicts with 'id' and 'content' keys
        """
        bm25_index = self.get_or_create_bm25_index(tenant_id)
        
        documents = [chunk['content'] for chunk in chunks]
        doc_ids = [chunk['id'] for chunk in chunks]
        
        bm25_index.build(documents, doc_ids)
        logger.info(f"Built BM25 index for tenant {tenant_id}")
    
    def add_to_bm25_index(
        self,
        tenant_id: str,
        chunk_id: str,
        content: str
    ) -> None:
        """Add a single chunk to BM25 index."""
        bm25_index = self.get_or_create_bm25_index(tenant_id)
        bm25_index.add_document(chunk_id, content)
    
    def clear_bm25_index(self, tenant_id: str) -> None:
        """Clear BM25 index for tenant."""
        if tenant_id in self._bm25_indexes:
            del self._bm25_indexes[tenant_id]
    
    async def hybrid_search(
        self,
        tenant_id: str,
        query: str,
        semantic_results: List[Tuple[str, float]],
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Perform hybrid search combining semantic and keyword results.
        
        Args:
            tenant_id: Tenant ID
            query: Search query
            semantic_results: Results from semantic search [(chunk_id, score), ...]
            top_k: Number of results to return
            
        Returns:
            List of (chunk_id, combined_score, score_breakdown) tuples
        """
        # Get BM25 results
        bm25_index = self.get_or_create_bm25_index(tenant_id)
        keyword_results = bm25_index.search(query, top_k=top_k * 2)
        
        # If no BM25 index, fall back to semantic only
        if not keyword_results:
            return [
                (chunk_id, score, {"semantic": score, "keyword": 0.0, "method": "semantic_only"})
                for chunk_id, score in semantic_results[:top_k]
            ]
        
        # Apply Reciprocal Rank Fusion
        combined = self._reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            top_k
        )
        
        return combined
    
    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[str, float]],
        keyword_results: List[Tuple[str, float]],
        top_k: int
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).
        
        RRF score = Σ (1 / (k + rank))
        """
        rrf_scores: Dict[str, float] = defaultdict(float)
        semantic_scores: Dict[str, float] = {}
        keyword_scores: Dict[str, float] = {}
        
        # Process semantic results
        for rank, (chunk_id, score) in enumerate(semantic_results, 1):
            rrf_scores[chunk_id] += self.SEMANTIC_WEIGHT * (1.0 / (self.RRF_K + rank))
            semantic_scores[chunk_id] = score
        
        # Process keyword results
        for rank, (chunk_id, score) in enumerate(keyword_results, 1):
            rrf_scores[chunk_id] += self.KEYWORD_WEIGHT * (1.0 / (self.RRF_K + rank))
            keyword_scores[chunk_id] = score
        
        # Sort by combined RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final results with score breakdown
        final_results = []
        for chunk_id, rrf_score in sorted_results[:top_k]:
            breakdown = {
                "semantic": semantic_scores.get(chunk_id, 0.0),
                "keyword": keyword_scores.get(chunk_id, 0.0),
                "rrf": rrf_score,
                "method": "hybrid"
            }
            final_results.append((chunk_id, rrf_score, breakdown))
        
        return final_results
    
    def normalize_scores(
        self,
        results: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """Normalize scores to 0-1 range."""
        if not results:
            return []
        
        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [(chunk_id, 1.0) for chunk_id, _ in results]
        
        return [
            (chunk_id, (score - min_score) / (max_score - min_score))
            for chunk_id, score in results
        ]
