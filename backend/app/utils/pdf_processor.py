"""
PDF text extraction using PyMuPDF (fitz).
Handles various PDF formats and extracts text preserving structure.
"""
import os
from typing import List, Tuple, Optional
from dataclasses import dataclass
import fitz  # PyMuPDF

from app.utils.logger import get_logger
from app.core.exceptions import DocumentProcessingError

logger = get_logger(__name__)


@dataclass
class PageContent:
    """Represents extracted content from a single page."""
    page_number: int
    text: str
    char_count: int


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""
    pages: List[PageContent]
    total_pages: int
    total_characters: int
    metadata: dict


class PDFProcessor:
    """
    PDF text extraction utility.
    Uses PyMuPDF for efficient and accurate text extraction.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def extract_text(self, file_path: str) -> PDFExtractionResult:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PDFExtractionResult with extracted text and metadata
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(
                f"PDF file not found: {file_path}",
                stage="file_access"
            )
        
        try:
            doc = fitz.open(file_path)
            pages: List[PageContent] = []
            total_characters = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text with layout preservation
                text = page.get_text("text", sort=True)
                
                # Clean up the text
                text = self._clean_text(text)
                
                if text.strip():
                    page_content = PageContent(
                        page_number=page_num + 1,  # 1-indexed
                        text=text,
                        char_count=len(text)
                    )
                    pages.append(page_content)
                    total_characters += len(text)
            
            # Extract metadata
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
            }
            
            doc.close()
            
            self.logger.info(
                "PDF extraction completed",
                file_path=file_path,
                total_pages=len(pages),
                total_characters=total_characters
            )
            
            return PDFExtractionResult(
                pages=pages,
                total_pages=len(pages),
                total_characters=total_characters,
                metadata=metadata
            )
            
        except fitz.FileDataError as e:
            raise DocumentProcessingError(
                f"Invalid or corrupted PDF file: {str(e)}",
                stage="pdf_parsing"
            )
        except Exception as e:
            self.logger.exception("PDF extraction failed", error=str(e))
            raise DocumentProcessingError(
                f"Failed to extract text from PDF: {str(e)}",
                stage="text_extraction"
            )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by normalizing whitespace and removing artifacts.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple spaces with single space
        import re
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove common artifacts
        text = text.replace('\x00', '')  # Null bytes
        text = text.replace('\ufeff', '')  # BOM
        
        return text.strip()
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get the number of pages in a PDF without full extraction.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Number of pages
        """
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to read PDF: {str(e)}",
                stage="page_count"
            )
    
    def validate_pdf(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a file is a valid PDF.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            doc = fitz.open(file_path)
            
            # Check if it has at least one page
            if len(doc) == 0:
                doc.close()
                return False, "PDF has no pages"
            
            # Try to access first page
            _ = doc[0].get_text()
            
            doc.close()
            return True, None
            
        except fitz.FileDataError:
            return False, "Invalid or corrupted PDF file"
        except Exception as e:
            return False, f"PDF validation failed: {str(e)}"
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> PDFExtractionResult:
        """
        Extract text from PDF bytes (useful for uploaded files).
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            PDFExtractionResult with extracted text
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages: List[PageContent] = []
            total_characters = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text", sort=True)
                text = self._clean_text(text)
                
                if text.strip():
                    page_content = PageContent(
                        page_number=page_num + 1,
                        text=text,
                        char_count=len(text)
                    )
                    pages.append(page_content)
                    total_characters += len(text)
            
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
            }
            
            doc.close()
            
            return PDFExtractionResult(
                pages=pages,
                total_pages=len(pages),
                total_characters=total_characters,
                metadata=metadata
            )
            
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to process PDF bytes: {str(e)}",
                stage="bytes_extraction"
            )
