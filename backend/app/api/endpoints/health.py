"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from app.services.ai_service import ai_service
from app.services.vector_service import VectorService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "SmartSPD",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@router.get("/health/ai")
async def ai_health_check() -> Dict[str, Any]:
    """AI service health check"""
    try:
        # Test AI service connection
        connection_test = await ai_service.test_connection()
        provider_info = ai_service.get_provider_info()
        
        return {
            "ai_service": connection_test,
            "provider_info": provider_info
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "ai_service": {"status": "failed"}
        }

@router.get("/health/services")
async def services_health_check() -> Dict[str, Any]:
    """Check all service dependencies"""
    health_status = {
        "overall_status": "healthy",
        "services": {}
    }
    
    # Check AI Service
    try:
        ai_test = await ai_service.test_connection()
        health_status["services"]["ai"] = ai_test
    except Exception as e:
        health_status["services"]["ai"] = {"status": "failed", "error": str(e)}
        health_status["overall_status"] = "degraded"
    
    # Check Vector Service
    try:
        vector_service = VectorService()
        if not vector_service.initialized:
            await vector_service.initialize()
        
        stats = await vector_service.get_index_stats()
        health_status["services"]["vector"] = {
            "status": "connected",
            "stats": stats
        }
    except Exception as e:
        health_status["services"]["vector"] = {"status": "failed", "error": str(e)}
        health_status["overall_status"] = "degraded"
    
    # Check Knowledge Graph Service
    try:
        kg_service = KnowledgeGraphService()
        if not kg_service.initialized:
            await kg_service.initialize()
        
        health_status["services"]["knowledge_graph"] = {"status": "connected"}
    except Exception as e:
        health_status["services"]["knowledge_graph"] = {"status": "failed", "error": str(e)}
        health_status["overall_status"] = "degraded"
    
    return health_status