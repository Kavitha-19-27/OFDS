"""
Highlight service for marking relevant text in responses.
Provides source attribution and evidence highlighting.
"""
from typing import List, Dict, Tuple, Optional
import re
from difflib import SequenceMatcher

from app.utils.logger import get_logger

logger = get_logger(__name__)


class HighlightService:
    """
    Service for highlighting relevant text and source attribution.
    Helps users verify information sources.
    """
    
    # Match threshold for considering text as sourced
    SIMILARITY_THRESHOLD = 0.6
    
    def highlight_sources(
        self,
        response: str,
        source_chunks: List[Dict]
    ) -> Dict:
        """
        Identify which parts of the response come from which sources.
        
        Args:
            response: Generated response text
            source_chunks: List of source chunks with 'content', 'document_id', etc.
            
        Returns:
            Dict with highlighted response and source attributions
        """
        # Split response into sentences
        sentences = self._split_sentences(response)
        
        attributions = []
        highlighted_sentences = []
        
        for sentence in sentences:
            # Find best matching source
            best_match = self._find_best_source_match(sentence, source_chunks)
            
            if best_match:
                source_idx, similarity, matched_text = best_match
                attributions.append({
                    'sentence': sentence,
                    'source_index': source_idx,
                    'similarity': round(similarity, 2),
                    'matched_text': matched_text[:200]  # Truncate for display
                })
                highlighted_sentences.append({
                    'text': sentence,
                    'has_source': True,
                    'source_index': source_idx
                })
            else:
                highlighted_sentences.append({
                    'text': sentence,
                    'has_source': False,
                    'source_index': None
                })
        
        # Calculate overall grounding score
        grounded_count = sum(1 for s in highlighted_sentences if s['has_source'])
        grounding_score = grounded_count / len(sentences) if sentences else 0
        
        return {
            'sentences': highlighted_sentences,
            'attributions': attributions,
            'grounding_score': round(grounding_score, 2),
            'total_sentences': len(sentences),
            'grounded_sentences': grounded_count
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter empty and very short
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _find_best_source_match(
        self,
        sentence: str,
        sources: List[Dict]
    ) -> Optional[Tuple[int, float, str]]:
        """
        Find the best matching source for a sentence.
        
        Returns:
            Tuple of (source_index, similarity_score, matched_text) or None
        """
        best_match = None
        best_score = 0
        best_text = ""
        
        sentence_lower = sentence.lower()
        
        for idx, source in enumerate(sources):
            content = source.get('content', '')
            content_lower = content.lower()
            
            # Quick check: any significant word overlap?
            sentence_words = set(re.findall(r'\b\w{4,}\b', sentence_lower))
            content_words = set(re.findall(r'\b\w{4,}\b', content_lower))
            
            word_overlap = len(sentence_words.intersection(content_words)) / len(sentence_words) if sentence_words else 0
            
            if word_overlap < 0.3:
                continue
            
            # Find best matching substring
            source_sentences = self._split_sentences(content)
            
            for source_sent in source_sentences:
                similarity = self._calculate_similarity(sentence_lower, source_sent.lower())
                
                if similarity > best_score and similarity >= self.SIMILARITY_THRESHOLD:
                    best_score = similarity
                    best_match = idx
                    best_text = source_sent
        
        if best_match is not None:
            return (best_match, best_score, best_text)
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Use SequenceMatcher for substring matching
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def create_inline_citations(
        self,
        response: str,
        source_chunks: List[Dict]
    ) -> str:
        """
        Add inline citations to response text.
        
        Example: "The project started in 2020 [1] and expanded globally [2]."
        """
        highlight_result = self.highlight_sources(response, source_chunks)
        
        # Build cited response
        cited_parts = []
        current_citations = set()
        
        for sent_info in highlight_result['sentences']:
            text = sent_info['text']
            
            if sent_info['has_source']:
                source_idx = sent_info['source_index']
                citation = f"[{source_idx + 1}]"
                
                # Add citation at end of sentence
                if text.endswith('.'):
                    text = text[:-1] + f" {citation}."
                else:
                    text = text + f" {citation}"
                
                current_citations.add(source_idx)
            
            cited_parts.append(text)
        
        return ' '.join(cited_parts)
    
    def generate_source_footnotes(
        self,
        source_chunks: List[Dict],
        cited_indices: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Generate footnotes for cited sources.
        """
        footnotes = []
        
        for idx, chunk in enumerate(source_chunks):
            if cited_indices is not None and idx not in cited_indices:
                continue
            
            # Get document info
            doc_id = chunk.get('document_id', 'Unknown')
            doc_name = chunk.get('document_name', f'Document {doc_id}')
            
            # Get preview of source text
            content = chunk.get('content', '')
            preview = content[:150] + '...' if len(content) > 150 else content
            
            footnotes.append({
                'index': idx + 1,
                'document_id': doc_id,
                'document_name': doc_name,
                'preview': preview,
                'chunk_id': chunk.get('chunk_id')
            })
        
        return footnotes
    
    def highlight_query_terms(
        self,
        text: str,
        query: str,
        highlight_start: str = "<mark>",
        highlight_end: str = "</mark>"
    ) -> str:
        """
        Highlight query terms in text.
        Useful for showing matching terms in source chunks.
        """
        # Extract significant query terms
        query_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))
        
        # Common stopwords to skip
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out'}
        query_terms -= stopwords
        
        # Build regex pattern
        if not query_terms:
            return text
        
        pattern = r'\b(' + '|'.join(re.escape(t) for t in query_terms) + r')\b'
        
        # Replace with highlighted version (case-insensitive)
        def highlighter(match):
            return f"{highlight_start}{match.group()}{highlight_end}"
        
        highlighted = re.sub(pattern, highlighter, text, flags=re.IGNORECASE)
        
        return highlighted
