"""
OpenAPI specification enhancements and custom documentation
"""
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
import json

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate enhanced OpenAPI specification with additional metadata"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        summary=getattr(app, 'summary', None),
        routes=app.routes,
        servers=getattr(app, 'servers', None),
        tags=getattr(app, 'openapi_tags', None),
    )
    
    # Add custom components and schemas
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from login endpoint"
        }
    }
    
    # Add security requirement to all endpoints
    if "security" not in openapi_schema:
        openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom responses
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Authentication token is missing or invalid",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "Unauthorized"},
                            "message": {"type": "string", "example": "Invalid or missing authentication token"},
                            "type": {"type": "string", "example": "authentication_error"}
                        }
                    }
                }
            }
        },
        "ForbiddenError": {
            "description": "User does not have permission to access this resource",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "Forbidden"},
                            "message": {"type": "string", "example": "Insufficient permissions"},
                            "type": {"type": "string", "example": "authorization_error"}
                        }
                    }
                }
            }
        },
        "ValidationError": {
            "description": "Request validation failed",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "Validation Error"},
                            "message": {"type": "string", "example": "Invalid input data"},
                            "type": {"type": "string", "example": "validation_error"},
                            "details": {
                                "type": "object",
                                "additionalProperties": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        "RateLimitError": {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "example": "Rate Limit Exceeded"},
                            "message": {"type": "string", "example": "Too many requests"},
                            "type": {"type": "string", "example": "rate_limit_error"},
                            "retry_after": {"type": "integer", "example": 60}
                        }
                    }
                }
            }
        }
    }
    
    # Add custom schemas
    openapi_schema["components"]["schemas"] = openapi_schema["components"].get("schemas", {})
    openapi_schema["components"]["schemas"].update({
        "PaginationMeta": {
            "type": "object",
            "properties": {
                "total": {"type": "integer", "description": "Total number of items"},
                "skip": {"type": "integer", "description": "Number of items skipped"},
                "limit": {"type": "integer", "description": "Maximum number of items returned"},
                "has_next": {"type": "boolean", "description": "Whether there are more items"}
            }
        },
        "APIResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "description": "Whether the request was successful"},
                "data": {"type": "object", "description": "Response data"},
                "message": {"type": "string", "description": "Human-readable message"},
                "meta": {"$ref": "#/components/schemas/PaginationMeta"}
            }
        },
        "UserRole": {
            "type": "string",
            "enum": ["tpa_admin", "cs_manager", "cs_agent", "member", "readonly"],
            "description": "User role with different permission levels"
        },
        "DocumentType": {
            "type": "string",
            "enum": ["spd", "bps", "certificate", "amendment", "other"],
            "description": "Type of health plan document"
        },
        "ProcessingStatus": {
            "type": "string",
            "enum": ["pending", "processing", "completed", "failed"],
            "description": "Document processing status"
        },
        "AuditSeverity": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "description": "Audit event severity level"
        }
    })
    
    # Add custom examples
    add_custom_examples(openapi_schema)
    
    # Add webhook documentation
    add_webhook_documentation(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def add_custom_examples(openapi_schema: Dict[str, Any]) -> None:
    """Add custom examples to OpenAPI schema"""
    
    # Add examples to common schemas
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]
        
        # Example for User schema
        if "User" in schemas:
            schemas["User"]["example"] = {
                "id": "user_123",
                "email": "john.doe@healthtpa.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "cs_agent",
                "tpa_id": "tpa_456",
                "is_active": True,
                "last_login_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        
        # Example for Document schema
        if "Document" in schemas:
            schemas["Document"]["example"] = {
                "id": "doc_789",
                "filename": "health_plan_spd_2024.pdf",
                "document_type": "spd",
                "file_size": 2048576,
                "processing_status": "completed",
                "health_plan_id": "plan_123",
                "uploaded_by": "user_123",
                "created_at": "2024-01-15T09:00:00Z"
            }

def add_webhook_documentation(openapi_schema: Dict[str, Any]) -> None:
    """Add webhook documentation to OpenAPI schema"""
    
    openapi_schema.setdefault("webhooks", {})
    
    openapi_schema["webhooks"] = {
        "document-processed": {
            "post": {
                "requestBody": {
                    "description": "Document processing completed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event": {"type": "string", "example": "document.processed"},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "document_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "processing_time_ms": {"type": "integer"}
                                        }
                                    },
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "signature": {"type": "string", "description": "HMAC signature for verification"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Webhook received successfully"
                    }
                }
            }
        },
        "query-completed": {
            "post": {
                "requestBody": {
                    "description": "AI query processing completed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event": {"type": "string", "example": "query.completed"},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "query_id": {"type": "string"},
                                            "user_id": {"type": "string"},
                                            "confidence_score": {"type": "number"},
                                            "response_time_ms": {"type": "integer"}
                                        }
                                    },
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "signature": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Webhook received successfully"
                    }
                }
            }
        }
    }

def generate_openapi_json(app: FastAPI, output_path: str = "openapi.json") -> None:
    """Generate and save OpenAPI specification to JSON file"""
    
    openapi_schema = custom_openapi(app)
    
    with open(output_path, 'w') as f:
        json.dump(openapi_schema, f, indent=2, default=str)
    
    print(f"OpenAPI specification saved to {output_path}")

def get_custom_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    oauth2_redirect_url: Optional[str] = None,
    init_oauth: Optional[Dict[str, Any]] = None,
    swagger_ui_parameters: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
    """Generate custom Swagger UI with enhanced styling and features"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
        <link rel="shortcut icon" href="{swagger_favicon_url}">
        <title>{title}</title>
        <style>
            .swagger-ui .topbar {{
                background-color: #1f2937;
            }}
            .swagger-ui .topbar .download-url-wrapper {{
                display: none;
            }}
            .swagger-ui .info .title {{
                color: #1f2937;
            }}
            .swagger-ui .scheme-container {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
            }}
            .swagger-ui .info .description {{
                margin: 20px 0;
            }}
            .topbar-wrapper img[alt="Swagger UI"] {{
                content: url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjQwIiB2aWV3Qm94PSIwIDAgMTIwIDQwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjEwIiB5PSIyNSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE2IiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0iI2ZmZmZmZiI+U21hcnRTUEQ8L3RleHQ+PC9zdmc+");
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui">
        </div>
        <script src="{swagger_js_url}"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '{openapi_url}',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            layout: "StandaloneLayout",
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            docExpansion: "none",
            defaultModelRendering: "example",
            defaultModelExpandDepth: 2,
            defaultModelsExpandDepth: 1,
            displayOperationId: false,
            tryItOutEnabled: true,
            supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
            {f'oauth2RedirectUrl: "{oauth2_redirect_url}",' if oauth2_redirect_url else ""}
            {f'initOAuth: {json.dumps(init_oauth)},' if init_oauth else ""}
            {f'configObject: {json.dumps(swagger_ui_parameters)},' if swagger_ui_parameters else ""}
        }})
        
        // Custom enhancements
        ui.preauthorizeApiKey('BearerAuth', 'Bearer your-jwt-token-here');
        
        // Add custom header
        const headerDiv = document.createElement('div');
        headerDiv.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
                <h1 style="margin: 0; font-size: 24px;">SmartSPD v2 API Documentation</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Enterprise-grade AI-powered health plan assistant for TPA operations</p>
                <div style="margin-top: 15px; font-size: 14px;">
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; margin-right: 10px;">
                        🔒 Authentication Required
                    </span>
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; margin-right: 10px;">
                        🏢 Multi-Tenant
                    </span>
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px;">
                        🔍 Rate Limited
                    </span>
                </div>
            </div>
        `;
        
        setTimeout(() => {{
            const infoDiv = document.querySelector('.swagger-ui .info');
            if (infoDiv) {{
                infoDiv.parentNode.insertBefore(headerDiv, infoDiv);
            }}
        }}, 100);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

def enhance_endpoint_documentation(app: FastAPI) -> None:
    """Add enhanced documentation to specific endpoints"""
    
    # This would be called after all routes are added
    for route in app.routes:
        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__name__'):
            endpoint_name = route.endpoint.__name__
            
            # Add custom documentation based on endpoint
            if endpoint_name == 'upload_document':
                if hasattr(route, 'openapi_extra'):
                    route.openapi_extra = route.openapi_extra or {}
                else:
                    route.openapi_extra = {}
                
                route.openapi_extra.update({
                    "description": """
                    Upload a document for AI processing and analysis.
                    
                    **Supported Formats:**
                    - PDF files (recommended)
                    - Microsoft Word documents (.docx)
                    - Plain text files (.txt)
                    
                    **Processing Pipeline:**
                    1. File validation and virus scanning
                    2. Text extraction and OCR (if needed)
                    3. AI-powered content analysis
                    4. Chunk creation for semantic search
                    5. Vector embedding generation
                    
                    **Rate Limits:**
                    - 3 concurrent uploads per user
                    - Maximum 10MB per file
                    - 50 uploads per hour per TPA
                    """,
                    "examples": {
                        "application/json": {
                            "summary": "Upload SPD document",
                            "value": {
                                "filename": "health_plan_spd_2024.pdf",
                                "document_type": "spd",
                                "health_plan_id": "plan_123"
                            }
                        }
                    }
                })

# Export the custom openapi function
__all__ = ["custom_openapi", "generate_openapi_json", "get_custom_swagger_ui_html", "enhance_endpoint_documentation"]