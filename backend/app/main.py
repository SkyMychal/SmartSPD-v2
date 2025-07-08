"""
SmartSPD FastAPI Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.audit import AuditMiddleware
from app.core.openapi import custom_openapi, get_custom_swagger_ui_html
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app with comprehensive metadata
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SmartSPD v2 - AI-Powered Health Plan Assistant for TPA Customer Service Operations",
    summary="Enterprise-grade RAG-based system for health insurance customer service automation",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    contact={
        "name": "SmartSPD Support",
        "email": "support@smartspd.com",
        "url": "https://smartspd.com/support"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://smartspd.com/license"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.smartspd.com",
            "description": "Production server"
        }
    ],
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "users",
            "description": "User management operations"
        },
        {
            "name": "tpas",
            "description": "Third Party Administrator (TPA) management"
        },
        {
            "name": "health-plans",
            "description": "Health plan configuration and management"
        },
        {
            "name": "documents",
            "description": "Document upload, processing, and management operations"
        },
        {
            "name": "chat",
            "description": "AI-powered chat and query operations"
        },
        {
            "name": "analytics",
            "description": "Performance analytics and reporting"
        },
        {
            "name": "admin",
            "description": "System administration operations (admin only)"
        },
        {
            "name": "audit",
            "description": "Audit trail and compliance logging (manager+ only)"
        },
        {
            "name": "user-activity",
            "description": "User activity tracking and behavioral analytics"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit middleware for automatic request tracking
app.add_middleware(AuditMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(AIServiceError)
async def ai_service_exception_handler(request: Request, exc: AIServiceError):
    logger.error(f"AI Service Error: {exc.message} (Service: {exc.service})")
    return JSONResponse(
        status_code=503,
        content={
            "error": "AI Service Unavailable",
            "message": exc.message,
            "service": exc.service,
            "type": "ai_service_error"
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error(f"Value Error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid Input",
            "message": str(exc),
            "type": "validation_error"
        }
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "SmartSPD API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/api/docs" if settings.DEBUG else "Documentation not available in production"
    }

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SmartSPD",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# Custom documentation endpoints
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling"""
    return get_custom_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{settings.APP_NAME} - API Documentation",
        oauth2_redirect_url="/api/docs/oauth2-redirect",
        init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
        },
    )

@app.get("/api/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    """Get the OpenAPI schema"""
    return custom_openapi(app)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"AI Provider: {settings.AI_SERVICE_PROVIDER}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SmartSPD API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )