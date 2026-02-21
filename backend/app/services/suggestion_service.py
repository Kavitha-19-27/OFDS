"""
Query suggestions service.
Generates contextual follow-up questions and query recommendations.
"""
from typing import List, Dict, Optional
import re
from collections import Counter

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SuggestionService:
    """
    Service for generating query suggestions.
    Helps users explore documents more effectively.
    """
    
    # Common follow-up question patterns
    FOLLOW_UP_PATTERNS = [
        "Can you explain more about {topic}?",
        "What are the key details of {topic}?",
        "How does {topic} work?",
        "What are the implications of {topic}?",
        "Can you compare {topic1} and {topic2}?",
        "What are the main points about {topic}?",
        "Summarize the section on {topic}",
        "What examples are given for {topic}?"
    ]
    
    def generate_suggestions(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict],
        num_suggestions: int = 3
    ) -> List[str]:
        """
        Generate contextual query suggestions.
        
        Args:
            query: Original user query
            response: Generated response
            context_chunks: Retrieved context chunks
            num_suggestions: Number of suggestions to generate
            
        Returns:
            List of suggested follow-up queries
        """
        suggestions = []
        
        # Extract topics from response and context
        topics = self._extract_topics(response, context_chunks)
        query_topics = self._extract_topics(query, [])
        
        # Filter out already-asked topics
        new_topics = [t for t in topics if t.lower() not in query.lower()]
        
        # Generate topic-based suggestions
        for topic in new_topics[:num_suggestions]:
            pattern = self.FOLLOW_UP_PATTERNS[len(suggestions) % len(self.FOLLOW_UP_PATTERNS)]
            suggestion = pattern.format(topic=topic, topic1=topic, topic2=topics[-1] if len(topics) > 1 else topic)
            suggestions.append(suggestion)
            
            if len(suggestions) >= num_suggestions:
                break
        
        # Add related concept suggestions
        if len(suggestions) < num_suggestions:
            related = self._find_related_concepts(response, context_chunks)
            for concept in related:
                if len(suggestions) >= num_suggestions:
                    break
                suggestion = f"What is the relationship between this and {concept}?"
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
        
        return suggestions[:num_suggestions]
    
    def generate_initial_suggestions(
        self,
        document_chunks: List[Dict],
        num_suggestions: int = 5
    ) -> List[str]:
        """
        Generate initial exploration suggestions for new documents.
        """
        suggestions = [
            "What are the main topics in this document?",
            "Summarize the key points of this document",
            "What conclusions or recommendations are made?"
        ]
        
        # Extract document-specific topics
        topics = self._extract_topics_from_chunks(document_chunks)
        
        for topic in topics[:3]:
            suggestions.append(f"Explain the section about {topic}")
        
        return suggestions[:num_suggestions]
    
    def _extract_topics(
        self,
        text: str,
        chunks: List[Dict]
    ) -> List[str]:
        """Extract key topics from text."""
        # Combine all text
        full_text = text + " " + " ".join(c.get('content', '') for c in chunks)
        
        # Extract capitalized phrases (likely proper nouns/topics)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', full_text)
        
        # Extract technical terms (words with specific patterns)
        technical = re.findall(r'\b[a-z]+(?:tion|ment|ity|ness|ing)\b', full_text.lower())
        
        # Count frequency
        all_terms = capitalized + [t.title() for t in technical]
        counter = Counter(all_terms)
        
        # Filter common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where', 'How', 'Why'}
        topics = [term for term, count in counter.most_common(10) if term not in common_words and len(term) > 3]
        
        return topics
    
    def _extract_topics_from_chunks(
        self,
        chunks: List[Dict]
    ) -> List[str]:
        """Extract topics specifically from document chunks."""
        topics = []
        
        for chunk in chunks[:10]:  # Sample first 10 chunks
            content = chunk.get('content', '')
            
            # Look for headings (common patterns)
            headings = re.findall(r'^#+\s*(.+)$', content, re.MULTILINE)
            headings += re.findall(r'^[A-Z][^.!?]*:(?=\s)', content, re.MULTILINE)
            
            for heading in headings:
                heading = heading.strip().rstrip(':')
                if len(heading) > 3 and len(heading) < 50:
                    topics.append(heading)
        
        return list(set(topics))[:5]
    
    def _find_related_concepts(
        self,
        response: str,
        chunks: List[Dict]
    ) -> List[str]:
        """Find concepts related to the response."""
        # Extract noun phrases from chunks that aren't in response
        chunk_text = " ".join(c.get('content', '') for c in chunks)
        response_lower = response.lower()
        
        # Simple noun phrase extraction (capitalized sequences)
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', chunk_text)
        
        # Filter those not mentioned in response
        new_concepts = [c for c in concepts if c.lower() not in response_lower]
        
        # Count and return top
        counter = Counter(new_concepts)
        return [c for c, _ in counter.most_common(3)]
    
    def generate_clarification_suggestions(
        self,
        query: str,
        ambiguous_terms: List[str]
    ) -> List[str]:
        """
        Generate clarification suggestions when query is ambiguous.
        """
        suggestions = []
        
        for term in ambiguous_terms[:3]:
            suggestions.append(f"Are you asking about {term} in the context of...?")
        
        # Add general clarifications
        if "how" in query.lower():
            suggestions.append("Do you want step-by-step instructions or a general overview?")
        
        if "what" in query.lower() and "difference" in query.lower():
            suggestions.append("Would you like a detailed comparison or a brief summary?")
        
        return suggestions[:3]
    
    def get_popular_queries(
        self,
        query_history: List[str],
        limit: int = 5
    ) -> List[str]:
        """
        Get popular/trending queries from history.
        """
        # Normalize and count queries
        normalized = [q.lower().strip() for q in query_history]
        counter = Counter(normalized)
        
        # Return most common (preserving original case)
        popular = []
        for normalized_q, count in counter.most_common(limit * 2):
            # Find original case version
            for orig in query_history:
                if orig.lower().strip() == normalized_q:
                    if orig not in popular:
                        popular.append(orig)
                        break
            if len(popular) >= limit:
                break
        
        return popular
