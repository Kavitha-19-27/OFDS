"""
FastAPI application entry point.
Configures middleware, routers, and application lifecycle events.
"""
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.exceptions import AppException, NotFoundError, ValidationError, AuthorizationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api.v1.router import api_router
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.core.middleware import error_handler_middleware, RateLimitMiddleware, RequestLoggingMiddleware
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def seed_platform_tenant():
    """Create Platform tenant and admin user if they don't exist."""
    async with AsyncSessionLocal() as session:
        # Check if platform tenant exists
        result = await session.execute(
            select(Tenant).where(Tenant.slug == "platform")
        )
        platform_tenant = result.scalar_one_or_none()
        
        if not platform_tenant:
            platform_tenant = Tenant(
                id=str(uuid.uuid4()),
                name="Platform",
                slug="platform",
                is_active=True
            )
            session.add(platform_tenant)
            await session.flush()
            logger.info("Created Platform tenant", tenant_id=platform_tenant.id)
        
        # Create default admin if doesn't exist
        result = await session.execute(
            select(User).where(User.email == "admin@rag.com")
        )
        existing_admin = result.scalar_one_or_none()
        
        if not existing_admin:
            admin = User(
                id=str(uuid.uuid4()),
                tenant_id=platform_tenant.id,
                email="admin@rag.com",
                hashed_password=hash_password("Admin@123"),
                full_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin)
            logger.info("Created default admin user: admin@rag.com")
        
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    
    Startup:
    - Initialize database
    - Create necessary directories
    
    Shutdown:
    - Cleanup resources
    """
    # Startup
    logger.info("Starting application", environment=settings.app_env)
    
    # Log CORS configuration for debugging
    logger.info("CORS origins configured", origins=settings.cors_origins_list)
    
    # Initialize database tables
    await init_db()
    logger.info("Database initialized")
    
    # Seed platform tenant and admin
    await seed_platform_tenant()
    logger.info("Platform tenant seeded")
    
    # Create data directories
    data_dirs = [
        Path("./data"),
        Path("./data/faiss_indexes"),
        Path("./data/uploads"),
    ]
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## RAG-based SaaS Application API
    
    A multi-tenant Retrieval-Augmented Generation (RAG) system that allows organizations to:
    
    - **Upload PDF documents** for processing and indexing
    - **Ask questions** and get AI-powered answers based on your documents
    - **Manage users** with role-based access control
    - **Track usage** and chat history
    
    ### Authentication
    
    All endpoints (except registration and login) require JWT authentication.
    Include the access token in the Authorization header:
    
    ```
    Authorization: Bearer <access_token>
    ```
    
    ### Multi-tenancy
    
    Each organization (tenant) has isolated data:
    - Documents and embeddings are tenant-scoped
    - Users can only access their tenant's data
    - Separate FAISS indexes per tenant
    
    ### Rate Limiting
    
    API calls are rate-limited to prevent abuse:
    - 100 requests per minute per IP (default)
    - Chat endpoint may have stricter limits
    """,
    version="1.0.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    openapi_url="/openapi.json" if settings.app_env != "production" else None,
    lifespan=lifespan,
)

# Add custom middleware - order matters!
# In FastAPI/Starlette, middleware is processed in REVERSE order (last added = first executed)
# So we add CORS LAST to ensure it runs FIRST and handles preflight requests

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute
)

# CORS must be added LAST so it runs FIRST (handles OPTIONS preflight before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check if the application is running and healthy.
    
    Returns basic status information.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env
    }


# Root endpoint
@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint"
)
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs" if settings.app_env != "production" else "disabled",
        "health": "/health"
    }


# Exception handler for application-specific errors
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle application-specific exceptions with proper status codes.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "development"
    )
