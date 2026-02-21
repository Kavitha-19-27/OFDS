"""
Middleware for error handling, rate limiting, and request logging.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.exceptions import AppException
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware.
    Catches all exceptions and returns consistent error responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            logger.error(
                "Application error",
                error_code=e.error_code,
                message=e.message,
                status_code=e.status_code,
                path=str(request.url.path)
            )
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.message,
                        "details": e.details
                    }
                }
            )
        except Exception as e:
            logger.exception(
                "Unhandled exception",
                error=str(e),
                path=str(request.url.path)
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": None
                    }
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all incoming requests and their response times.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            query_params=str(request.query_params),
            client_ip=get_remote_address(request)
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log request completion
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Extracts tenant context from JWT and adds to request state.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Initialize tenant context as None
        request.state.tenant_id = None
        request.state.user_id = None
        request.state.user_role = None
        
        # Process request (auth will set these values)
        response = await call_next(request)
        return response


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    logger.warning(
        "Rate limit exceeded",
        client_ip=get_remote_address(request),
        path=str(request.url.path)
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {"retry_after_seconds": 60}
            }
        }
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory tracking.
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {ip: [(timestamp, ...), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = get_remote_address(request)
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old requests and count recent ones
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] if ts > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path=str(request.url.path)
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "details": {"retry_after_seconds": 60}
                    }
                }
            )
        
        # Record this request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)


# Alias for backward compatibility
error_handler_middleware = ErrorHandlerMiddleware
