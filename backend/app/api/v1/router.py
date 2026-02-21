"""
API v1 router aggregating all endpoint modules.
"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.enhanced import router as enhanced_router
from app.api.v1.trial import router as trial_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tenants_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(enhanced_router)
api_router.include_router(trial_router)  # No auth required for trial

