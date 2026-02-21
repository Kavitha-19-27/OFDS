"""
Confidence scoring service for RAG responses.
Evaluates retrieval quality and answer confidence.
"""
from typing import List, Dict, Optional
from enum import Enum
import re
import asyncio

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level categories."""
    HIGH = "high"           # 0.8+ score
    MEDIUM = "medium"       # 0.5-0.8 score
    LOW = "low"            # 0.3-0.5 score
    NONE = "none"          # <0.3 score - likely no relevant info


class ConfidenceService:
    """
    Service for calculating confidence scores for RAG responses.
    Uses multiple signals to determine answer reliability.
    """
    
    # Confidence thresholds
    HIGH_THRESHOLD = 0.8
    MEDIUM_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.3
    
    async def calculate_confidence(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        answer: Optional[str] = None
    ) -> Dict:
        """
        Calculate confidence score for a query response.
        
        Args:
            query: Original user query
            retrieved_chunks: List of chunks with 'content' and 'score'
            answer: Generated answer (optional, for additional signals)
            
        Returns:
            Dict with confidence_score, level, signals, and explanation
        """
        if not retrieved_chunks:
            return {
                'confidence_score': 0.0,
                'confidence_level': ConfidenceLevel.NONE.value,
                'signals': {},
                'explanation': 'No relevant documents found'
            }
        
        # Calculate individual signals
        signals = {
            'retrieval_score': self._retrieval_score(retrieved_chunks),
            'coverage': self._query_coverage(query, retrieved_chunks),
            'consistency': self._chunk_consistency(retrieved_chunks),
            'specificity': self._content_specificity(query, retrieved_chunks),
            'redundancy': self._answer_redundancy(retrieved_chunks)
        }
        
        # Add answer-based signals if available
        if answer:
            signals['grounding'] = self._answer_grounding(answer, retrieved_chunks)
            signals['completeness'] = self._answer_completeness(query, answer)
        
        # Calculate weighted confidence score
        weights = {
            'retrieval_score': 0.25,
            'coverage': 0.20,
            'consistency': 0.15,
            'specificity': 0.15,
            'redundancy': 0.10,
            'grounding': 0.10,
            'completeness': 0.05
        }
        
        confidence_score = sum(
            signals.get(key, 0) * weight 
            for key, weight in weights.items()
        )
        
        # Determine confidence level
        confidence_level = self._get_confidence_level(confidence_score)
        
        # Generate explanation
        explanation = self._generate_explanation(signals, confidence_level)
        
        return {
            'confidence_score': round(confidence_score, 3),
            'confidence_level': confidence_level.value,
            'signals': {k: round(v, 3) for k, v in signals.items()},
            'explanation': explanation
        }
    
    def _retrieval_score(self, chunks: List[Dict]) -> float:
        """Average retrieval score of top chunks."""
        if not chunks:
            return 0.0
        
        scores = [c.get('score', 0) for c in chunks]
        # Normalize scores (assuming they're in 0-1 range)
        avg_score = sum(scores) / len(scores)
        
        # Top-score weighted average (emphasize best matches)
        if len(scores) >= 2:
            weighted_avg = 0.5 * max(scores) + 0.3 * sorted(scores)[-2] + 0.2 * avg_score
            return min(1.0, weighted_avg)
        
        return min(1.0, avg_score)
    
    def _query_coverage(self, query: str, chunks: List[Dict]) -> float:
        """How well do chunks cover the query terms."""
        query_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))
        if not query_terms:
            return 0.5  # Neutral for very short queries
        
        combined_content = ' '.join(c.get('content', '') for c in chunks).lower()
        content_terms = set(re.findall(r'\b\w{3,}\b', combined_content))
        
        covered = query_terms.intersection(content_terms)
        return len(covered) / len(query_terms)
    
    def _chunk_consistency(self, chunks: List[Dict]) -> float:
        """
        Check if chunks are semantically consistent.
        Low consistency might indicate contradictory sources.
        """
        if len(chunks) < 2:
            return 0.8  # Single chunk - assume consistent
        
        # Simple approach: check keyword overlap between chunks
        chunk_terms = []
        for chunk in chunks:
            content = chunk.get('content', '')
            terms = set(re.findall(r'\b\w{4,}\b', content.lower()))
            chunk_terms.append(terms)
        
        # Calculate pairwise overlap
        overlaps = []
        for i in range(len(chunk_terms)):
            for j in range(i + 1, len(chunk_terms)):
                if chunk_terms[i] and chunk_terms[j]:
                    union = chunk_terms[i].union(chunk_terms[j])
                    intersect = chunk_terms[i].intersection(chunk_terms[j])
                    overlap = len(intersect) / len(union) if union else 0
                    overlaps.append(overlap)
        
        if not overlaps:
            return 0.5
        
        # Some overlap is good (consistent), but not too much (redundant)
        avg_overlap = sum(overlaps) / len(overlaps)
        # Ideal overlap: 0.1-0.4
        if 0.1 <= avg_overlap <= 0.4:
            return 1.0
        elif avg_overlap < 0.1:
            return 0.5 + avg_overlap * 5  # Low consistency penalty
        else:
            return max(0.5, 1.0 - (avg_overlap - 0.4))  # High redundancy penalty
    
    def _content_specificity(self, query: str, chunks: List[Dict]) -> float:
        """
        Check if content is specific to the query topic.
        Generic content gets lower scores.
        """
        # Extract likely topic entities from query
        query_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query))
        query_terms = set(re.findall(r'\b\w{5,}\b', query.lower()))
        
        combined_content = ' '.join(c.get('content', '') for c in chunks)
        
        # Count specific term occurrences
        specificity_score = 0
        for entity in query_entities:
            if entity.lower() in combined_content.lower():
                specificity_score += 0.2
        
        for term in query_terms:
            if term in combined_content.lower():
                specificity_score += 0.1
        
        return min(1.0, specificity_score)
    
    def _answer_redundancy(self, chunks: List[Dict]) -> float:
        """
        Multiple sources supporting same answer increases confidence.
        """
        if len(chunks) < 2:
            return 0.5
        
        # Use sentence-level overlap as proxy for agreement
        sentences = []
        for chunk in chunks:
            content = chunk.get('content', '')
            chunk_sentences = re.split(r'[.!?]+', content)
            sentences.extend([s.strip().lower() for s in chunk_sentences if len(s.strip()) > 20])
        
        if len(sentences) < 2:
            return 0.5
        
        # Check for similar sentences across chunks
        similar_pairs = 0
        for i, s1 in enumerate(sentences):
            for s2 in sentences[i+1:]:
                words1 = set(s1.split())
                words2 = set(s2.split())
                if words1 and words2:
                    similarity = len(words1.intersection(words2)) / len(words1.union(words2))
                    if similarity > 0.5:
                        similar_pairs += 1
        
        # Some redundancy is good
        if similar_pairs == 0:
            return 0.5
        elif similar_pairs <= 3:
            return 0.8 + 0.1 * similar_pairs
        else:
            return 1.0
    
    def _answer_grounding(self, answer: str, chunks: List[Dict]) -> float:
        """Check if answer content is grounded in retrieved chunks."""
        if not answer:
            return 0.5
        
        combined_content = ' '.join(c.get('content', '') for c in chunks).lower()
        
        # Extract key phrases from answer
        answer_sentences = re.split(r'[.!?]+', answer)
        grounded_count = 0
        total_count = 0
        
        for sentence in answer_sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            total_count += 1
            # Check if key terms from sentence appear in context
            terms = re.findall(r'\b\w{4,}\b', sentence.lower())
            if not terms:
                continue
            
            matches = sum(1 for t in terms if t in combined_content)
            if matches / len(terms) > 0.5:
                grounded_count += 1
        
        if total_count == 0:
            return 0.5
        
        return grounded_count / total_count
    
    def _answer_completeness(self, query: str, answer: str) -> float:
        """Check if answer appears to address the query."""
        if not answer:
            return 0.0
        
        # Basic heuristics
        answer_length = len(answer)
        
        # Very short answers are likely incomplete
        if answer_length < 50:
            return 0.3
        elif answer_length < 150:
            return 0.6
        elif answer_length < 500:
            return 0.9
        else:
            return 1.0
    
    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= self.HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif score >= self.MEDIUM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        elif score >= self.LOW_THRESHOLD:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.NONE
    
    def _generate_explanation(
        self,
        signals: Dict[str, float],
        level: ConfidenceLevel
    ) -> str:
        """Generate human-readable explanation for confidence level."""
        strong_signals = [k for k, v in signals.items() if v >= 0.8]
        weak_signals = [k for k, v in signals.items() if v < 0.4]
        
        if level == ConfidenceLevel.HIGH:
            return f"High confidence based on strong retrieval and good coverage."
        elif level == ConfidenceLevel.MEDIUM:
            if weak_signals:
                return f"Medium confidence. Lower scores in: {', '.join(weak_signals)}"
            return "Medium confidence based on moderate retrieval quality."
        elif level == ConfidenceLevel.LOW:
            return f"Low confidence. Weak signals: {', '.join(weak_signals)}"
        else:
            return "Very low confidence. Retrieved content may not be relevant."
