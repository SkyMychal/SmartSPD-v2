"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, admin, auth, users, tpas, health_plans, documents, chat, analytics, audit, user_activity, simple_upload, feedback

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tpas.router, prefix="/tpas", tags=["tpas"])
api_router.include_router(health_plans.router, prefix="/health-plans", tags=["health-plans"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(user_activity.router, prefix="/user-activity", tags=["user-activity"])
api_router.include_router(simple_upload.router, prefix="/upload", tags=["simple-upload"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])