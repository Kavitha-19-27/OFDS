"""
Database connection and session management.
Supports SQLite for development and PostgreSQL for production.
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_engine() -> AsyncEngine:
    """
    Create and configure the async database engine.
    Uses different configurations for SQLite vs PostgreSQL.
    """
    db_url = settings.database_url
    
    # Convert postgresql:// to postgresql+asyncpg:// for async support
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    is_sqlite = db_url.startswith("sqlite")
    
    engine_kwargs = {
        "echo": settings.debug,
    }
    
    if is_sqlite:
        # SQLite-specific settings for async support
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        })
    else:
        # PostgreSQL connection pool settings
        engine_kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })
    
    return create_async_engine(db_url, **engine_kwargs)


# Create engine instance
engine = get_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Properly handles session lifecycle with automatic cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for backward compatibility
get_async_session = get_db


async def init_db() -> None:
    """
    Initialize database tables.
    Should be called on application startup.
    """
    # Only create data directory for SQLite
    if settings.database_url.startswith("sqlite"):
        data_dir = os.path.dirname(settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", ""))
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models import (  # noqa: F401
            tenant, user, document, chat_log,
            audit_log, chat_feedback, chat_template,
            document_access, document_summary, ingestion_queue,
            query_cache, retention_policy, retrieval_metrics, tenant_quota
        )
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    Should be called on application shutdown.
    """
    await engine.dispose()
