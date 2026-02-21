"""
Custom exception classes for the application.
Maps to appropriate HTTP status codes.
"""
from typing import Optional, Any


class AppException(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(AppException):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class NotFoundError(AppException):
    """Raised when a resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details if details else None
        )


class ValidationError(AppException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[list] = None
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"errors": errors} if errors else None
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after} if retry_after else None
        )


class ConflictError(AppException):
    """Raised when there's a resource conflict."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


class TenantLimitError(AppException):
    """Raised when tenant resource limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Tenant resource limit exceeded",
        limit_type: Optional[str] = None,
        current_value: Optional[int] = None,
        max_value: Optional[int] = None
    ):
        details = {}
        if limit_type:
            details["limit_type"] = limit_type
        if current_value is not None:
            details["current_value"] = current_value
        if max_value is not None:
            details["max_value"] = max_value
            
        super().__init__(
            message=message,
            status_code=403,
            error_code="TENANT_LIMIT_EXCEEDED",
            details=details if details else None
        )


class ExternalServiceError(AppException):
    """Raised when an external service call fails."""
    
    def __init__(
        self,
        message: str = "External service error",
        service: Optional[str] = None,
        details: Optional[Any] = None
    ):
        _details = {"service": service} if service else {}
        if details:
            _details.update(details if isinstance(details, dict) else {"info": details})
            
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=_details if _details else None
        )


class DocumentProcessingError(AppException):
    """Raised when document processing fails."""
    
    def __init__(
        self,
        message: str = "Document processing failed",
        document_id: Optional[str] = None,
        stage: Optional[str] = None
    ):
        details = {}
        if document_id:
            details["document_id"] = document_id
        if stage:
            details["stage"] = stage
            
        super().__init__(
            message=message,
            status_code=500,
            error_code="DOCUMENT_PROCESSING_ERROR",
            details=details if details else None
        )


class StorageLimitExceededError(AppException):
    """Raised when storage limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Storage limit exceeded",
        current_size: Optional[int] = None,
        max_size: Optional[int] = None
    ):
        details = {}
        if current_size is not None:
            details["current_size"] = current_size
        if max_size is not None:
            details["max_size"] = max_size
            
        super().__init__(
            message=message,
            status_code=413,
            error_code="STORAGE_LIMIT_EXCEEDED",
            details=details if details else None
        )


# Aliases for backward compatibility
ResourceNotFoundError = NotFoundError
DuplicateResourceError = ConflictError
