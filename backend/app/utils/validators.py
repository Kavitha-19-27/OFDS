"""
Input validation utilities for file uploads and user inputs.
"""
import os
import hashlib
import re
from typing import Tuple, Optional
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import ValidationError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# PDF magic bytes
PDF_MAGIC_BYTES = b'%PDF'

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'application/pdf': ['.pdf'],
}


async def validate_file_upload(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded file.
    
    Checks:
    - File size
    - File extension
    - MIME type
    - Magic bytes
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename
    if not file.filename:
        return False, "Filename is required"
    
    # Sanitize filename
    filename = sanitize_filename(file.filename)
    
    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.allowed_extensions_list:
        return False, f"File extension '{ext}' not allowed. Allowed: {settings.allowed_extensions}"
    
    # Read file content for validation
    content = await file.read()
    await file.seek(0)  # Reset file pointer
    
    # Check file size
    file_size = len(content)
    if file_size > settings.max_file_size_bytes:
        return False, f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({settings.max_file_size_mb}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Check magic bytes for PDF
    if ext == '.pdf':
        if not content.startswith(PDF_MAGIC_BYTES):
            return False, "File content does not match PDF format"
    
    # Check MIME type
    content_type = file.content_type or ''
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Be lenient - some browsers send wrong MIME types
        logger.warning(
            "Unexpected MIME type",
            mime_type=content_type,
            filename=filename
        )
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename if filename else "unnamed_file"


def compute_file_hash(content: bytes) -> str:
    """
    Compute SHA-256 hash of file content.
    
    Args:
        content: File content as bytes
        
    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(content).hexdigest()


def validate_tenant_slug(slug: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a tenant slug.
    
    Args:
        slug: Tenant slug to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not slug:
        return False, "Slug is required"
    
    if len(slug) < 2:
        return False, "Slug must be at least 2 characters"
    
    if len(slug) > 100:
        return False, "Slug must be at most 100 characters"
    
    if not re.match(r'^[a-z0-9-]+$', slug):
        return False, "Slug can only contain lowercase letters, numbers, and hyphens"
    
    if slug.startswith('-') or slug.endswith('-'):
        return False, "Slug cannot start or end with a hyphen"
    
    if '--' in slug:
        return False, "Slug cannot contain consecutive hyphens"
    
    return True, None


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email:
        return False, "Email is required"
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 255:
        return False, "Email is too long"
    
    return True, None


def validate_file_extension(filename: str, allowed_extensions: list = None) -> None:
    """
    Validate file extension.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.pdf'])
        
    Raises:
        ValidationError: If extension is not allowed
    """
    if not filename:
        raise ValidationError("Filename is required")
    
    ext = os.path.splitext(filename)[1].lower()
    
    # Use provided extensions or settings default
    valid_extensions = allowed_extensions or settings.allowed_extensions_list
    
    if ext not in valid_extensions:
        raise ValidationError(f"File extension '{ext}' not allowed. Allowed: {valid_extensions}")


def validate_file_size(file_size: int, max_size_mb: int = None) -> None:
    """
    Validate file size.
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB (optional, uses settings default)
        
    Raises:
        ValidationError: If file size exceeds limit
    """
    if file_size <= 0:
        raise ValidationError("File is empty")
    
    max_bytes = (max_size_mb * 1024 * 1024) if max_size_mb else settings.max_file_size_bytes
    max_mb = max_size_mb or settings.max_file_size_mb
    
    if file_size > max_bytes:
        size_mb = file_size / (1024 * 1024)
        raise ValidationError(f"File size ({size_mb:.2f}MB) exceeds limit ({max_mb}MB)")
