"""
Startup script for Render deployment.
Initializes database and creates necessary directories.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base, init_db
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_startup():
    """Initialize application for production deployment."""
    logger.info("Starting production initialization...")
    
    # Create data directories
    data_dirs = [
        Path("./data"),
        Path("./data/faiss_indexes"),
        Path("./data/uploads"),
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    logger.info("Startup initialization completed successfully")


def main():
    """Main entry point for startup script."""
    print("=" * 50)
    print("RAG SaaS - Production Startup")
    print("=" * 50)
    print(f"Environment: {settings.app_env}")
    print(f"Database URL: {settings.database_url[:30]}...")
    print("=" * 50)
    
    asyncio.run(run_startup())
    
    print("Startup completed successfully!")


if __name__ == "__main__":
    main()
