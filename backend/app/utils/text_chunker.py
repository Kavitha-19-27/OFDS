"""
Deterministic text chunking for RAG pipeline.
Splits text into chunks with overlap for better retrieval.
"""
import re
from typing import List, Optional
from dataclasses import dataclass
import tiktoken

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """Represents a single text chunk."""
    index: int
    content: str
    token_count: int
    page_number: Optional[int]
    start_char: int
    end_char: int


class TextChunker:
    """
    Text chunking utility for RAG applications.
    Uses tiktoken for accurate token counting and sentence-aware splitting.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = 100
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target tokens per chunk (default from settings)
            chunk_overlap: Overlap tokens between chunks (default from settings)
            min_chunk_size: Minimum tokens for a valid chunk
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Use cl100k_base encoding (same as OpenAI's text-embedding models)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Sentence splitting pattern
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|'  # Standard sentence endings
            r'(?<=[.!?])\s*\n+|'         # Sentence ending + newline
            r'\n\n+'                      # Paragraph breaks
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def chunk_text(
        self,
        text: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[TextChunk]:
        """
        Split text into chunks with overlap.
        
        Uses sentence-aware splitting to avoid cutting mid-sentence.
        
        Args:
            text: Full text to chunk
            page_numbers: Optional list mapping character positions to page numbers
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        chunks: List[TextChunk] = []
        current_chunk_sentences: List[str] = []
        current_token_count = 0
        chunk_start_char = 0
        current_char_position = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If single sentence exceeds chunk size, split it
            if sentence_tokens > self.chunk_size:
                # First, save current chunk if not empty
                if current_chunk_sentences:
                    chunk_text = ' '.join(current_chunk_sentences)
                    chunks.append(TextChunk(
                        index=len(chunks),
                        content=chunk_text,
                        token_count=current_token_count,
                        page_number=self._get_page_number(chunk_start_char, page_numbers),
                        start_char=chunk_start_char,
                        end_char=current_char_position
                    ))
                    current_chunk_sentences = []
                    current_token_count = 0
                
                # Split long sentence into smaller pieces
                sub_chunks = self._split_long_sentence(sentence)
                for sub_chunk in sub_chunks:
                    sub_token_count = self.count_tokens(sub_chunk)
                    chunks.append(TextChunk(
                        index=len(chunks),
                        content=sub_chunk,
                        token_count=sub_token_count,
                        page_number=self._get_page_number(current_char_position, page_numbers),
                        start_char=current_char_position,
                        end_char=current_char_position + len(sub_chunk)
                    ))
                    current_char_position += len(sub_chunk) + 1
                
                chunk_start_char = current_char_position
                continue
            
            # Check if adding this sentence would exceed chunk size
            if current_token_count + sentence_tokens > self.chunk_size and current_chunk_sentences:
                # Save current chunk
                chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(TextChunk(
                    index=len(chunks),
                    content=chunk_text,
                    token_count=current_token_count,
                    page_number=self._get_page_number(chunk_start_char, page_numbers),
                    start_char=chunk_start_char,
                    end_char=current_char_position
                ))
                
                # Calculate overlap - keep last N tokens worth of sentences
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk_sentences,
                    self.chunk_overlap
                )
                
                current_chunk_sentences = overlap_sentences
                current_token_count = sum(
                    self.count_tokens(s) for s in overlap_sentences
                )
                chunk_start_char = current_char_position - sum(
                    len(s) + 1 for s in overlap_sentences
                )
            
            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens
            current_char_position += len(sentence) + 1
        
        # Don't forget the last chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            if self.count_tokens(chunk_text) >= self.min_chunk_size:
                chunks.append(TextChunk(
                    index=len(chunks),
                    content=chunk_text,
                    token_count=current_token_count,
                    page_number=self._get_page_number(chunk_start_char, page_numbers),
                    start_char=chunk_start_char,
                    end_char=current_char_position
                ))
        
        # Re-index chunks
        for i, chunk in enumerate(chunks):
            chunk.index = i
        
        logger.info(
            "Text chunking completed",
            total_chunks=len(chunks),
            avg_tokens=sum(c.token_count for c in chunks) // len(chunks) if chunks else 0
        )
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # First split by the pattern
        parts = self.sentence_pattern.split(text)
        
        # Clean and filter
        sentences = []
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)
        
        return sentences
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a long sentence into smaller chunks."""
        tokens = self.encoding.encode(sentence)
        chunks = []
        
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text.strip())
        
        return chunks
    
    def _get_overlap_sentences(
        self,
        sentences: List[str],
        target_tokens: int
    ) -> List[str]:
        """Get sentences from the end that sum to approximately target tokens."""
        overlap = []
        token_count = 0
        
        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if token_count + sentence_tokens <= target_tokens:
                overlap.insert(0, sentence)
                token_count += sentence_tokens
            else:
                break
        
        return overlap
    
    def _get_page_number(
        self,
        char_position: int,
        page_numbers: Optional[List[int]]
    ) -> Optional[int]:
        """Get page number for a character position."""
        if not page_numbers:
            return None
        
        # page_numbers should be a list where index is char position
        # For simplicity, find the nearest mapping
        if char_position < len(page_numbers):
            return page_numbers[char_position]
        return page_numbers[-1] if page_numbers else None
    
    def chunk_pages(
        self,
        pages: List[dict]
    ) -> List[TextChunk]:
        """
        Chunk text from multiple pages, tracking page numbers.
        
        Args:
            pages: List of dicts with 'text' and 'page_number' keys
            
        Returns:
            List of TextChunk objects with page tracking
        """
        # Build combined text and page number mapping
        combined_text = ""
        page_number_map: List[int] = []
        
        for page in pages:
            page_text = page.get("text", "")
            page_num = page.get("page_number", 1)
            
            start_pos = len(combined_text)
            combined_text += page_text + "\n\n"
            
            # Map each character position to its page number
            page_number_map.extend([page_num] * (len(page_text) + 2))
        
        return self.chunk_text(combined_text, page_number_map)
