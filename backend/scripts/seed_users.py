"""
Seed script to create admin users.
Run with: python -m scripts.seed_users
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import hash_password
import uuid


async def seed_users():
    """Create default admin users."""
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Check if platform tenant exists
        result = await session.execute(
            select(Tenant).where(Tenant.name == "Platform")
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
            print(f"Created Platform tenant: {platform_tenant.id}")
        
        # Create Admin
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
            print("Created Admin: admin@rag.com / Admin@123")
        else:
            print("Admin already exists")
        
        await session.commit()
        print("\nSeed completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_users())
