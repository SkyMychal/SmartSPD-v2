"""
Main API router
"""
from fastapi import APIRouter

from app.api.endpoints import health, chat

api_router = APIRouter()

# Health check endpoints
api_router.include_router(health.router, tags=["health"])

# Chat endpoints
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# TODO: Add other endpoint routers here
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(tpa.router, prefix="/tpa", tags=["tpa"])
# api_router.include_router(health_plan.router, prefix="/health-plans", tags=["health_plans"])
# api_router.include_router(document.router, prefix="/documents", tags=["documents"])