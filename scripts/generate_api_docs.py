#!/usr/bin/env python3
"""
Generate comprehensive API documentation for SmartSPD v2

This script creates:
1. OpenAPI JSON specification
2. Markdown documentation
3. Postman collection
4. API testing guide
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.openapi import custom_openapi, generate_openapi_json

def generate_documentation():
    """Generate all API documentation files"""
    
    # Create docs directory
    docs_dir = Path(__file__).parent.parent / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Generating SmartSPD v2 API Documentation...")
    
    # 1. Generate OpenAPI JSON
    print("📄 Generating OpenAPI specification...")
    openapi_path = docs_dir / "openapi.json"
    generate_openapi_json(app, str(openapi_path))
    
    # 2. Generate Markdown documentation
    print("📝 Generating Markdown documentation...")
    generate_markdown_docs(docs_dir)
    
    # 3. Generate Postman collection
    print("📮 Generating Postman collection...")
    generate_postman_collection(docs_dir)
    
    # 4. Generate API testing guide
    print("🧪 Generating API testing guide...")
    generate_testing_guide(docs_dir)
    
    # 5. Generate API reference
    print("📚 Generating API reference...")
    generate_api_reference(docs_dir)
    
    print(f"✅ Documentation generated successfully in {docs_dir}")
    print(f"🌐 View documentation at: file://{docs_dir.absolute()}/index.html")

def generate_markdown_docs(docs_dir: Path):
    """Generate comprehensive Markdown documentation"""
    
    openapi_schema = custom_openapi(app)
    
    # Main API documentation
    api_docs = f"""# SmartSPD v2 API Documentation

{openapi_schema.get('info', {}).get('description', '')}

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.smartspd.com`

## Authentication
All API endpoints require JWT Bearer token authentication.

```bash
Authorization: Bearer <your-jwt-token>
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user info

### Users
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{{id}}` - Get user by ID
- `PUT /api/v1/users/{{id}}` - Update user
- `DELETE /api/v1/users/{{id}}` - Delete user

### Documents
- `POST /api/v1/documents/upload` - Upload single document
- `POST /api/v1/documents/batch/upload` - Upload multiple documents
- `POST /api/v1/documents/batch/zip` - Upload ZIP archive
- `GET /api/v1/documents/{{id}}` - Get document details
- `GET /api/v1/documents/{{id}}/download` - Download document
- `POST /api/v1/documents/{{id}}/versions/upload` - Upload new version

### Chat & AI
- `POST /api/v1/chat/query` - Submit AI query
- `GET /api/v1/chat/conversations` - List conversations
- `GET /api/v1/chat/suggestions` - Get query suggestions

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard statistics
- `GET /api/v1/analytics/report` - Comprehensive analytics
- `POST /api/v1/analytics/feedback` - Submit feedback

### Admin
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/metrics` - System metrics
- `GET /api/v1/admin/users` - User management
- `GET /api/v1/admin/tpas` - TPA management

### Audit
- `GET /api/v1/audit/logs` - View audit logs
- `GET /api/v1/audit/summary` - Audit summary
- `POST /api/v1/audit/export` - Export audit data

### User Activity
- `GET /api/v1/user-activity/summary/{{user_id}}` - User activity summary
- `GET /api/v1/user-activity/tpa-overview` - TPA activity overview
- `GET /api/v1/user-activity/engagement-metrics` - Engagement metrics
- `GET /api/v1/user-activity/feature-usage` - Feature usage analytics

## Error Responses

All error responses follow a consistent format:

```json
{{
  "error": "Error Type",
  "message": "Human-readable error message",
  "type": "error_code",
  "details": {{}}
}}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limits
- **General**: 100 requests per minute per user
- **File Upload**: 10 uploads per minute per user
- **AI Queries**: 30 queries per minute per user
- **Admin Operations**: 20 requests per minute per admin

## Pagination
Most list endpoints support pagination:

```
GET /api/v1/users?skip=0&limit=50
```

Response format:
```json
{{
  "items": [...],
  "meta": {{
    "total": 150,
    "skip": 0,
    "limit": 50,
    "has_next": true
  }}
}}
```

## WebSocket Endpoints
- `ws://localhost:8000/ws/chat` - Real-time chat
- `ws://localhost:8000/ws/processing` - Document processing updates

## Webhooks
SmartSPD supports webhooks for event notifications:

### Document Processing Events
```json
{{
  "event": "document.processed",
  "data": {{
    "document_id": "doc_123",
    "status": "completed",
    "processing_time_ms": 5000
  }},
  "timestamp": "2024-01-15T10:30:00Z"
}}
```

### Query Completion Events
```json
{{
  "event": "query.completed",
  "data": {{
    "query_id": "query_456",
    "user_id": "user_123",
    "confidence_score": 0.95,
    "response_time_ms": 1200
  }},
  "timestamp": "2024-01-15T10:30:05Z"
}}
```

## SDK and Libraries
- **Python**: `pip install smartspd-client`
- **Node.js**: `npm install smartspd-client`
- **cURL Examples**: See testing guide

## Support
- **Documentation**: [SmartSPD Docs](https://docs.smartspd.com)
- **API Issues**: [GitHub Issues](https://github.com/smartspd/api/issues)
- **Email Support**: api-support@smartspd.com

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(docs_dir / "README.md", "w") as f:
        f.write(api_docs)

def generate_postman_collection(docs_dir: Path):
    """Generate Postman collection for API testing"""
    
    openapi_schema = custom_openapi(app)
    
    collection = {
        "info": {
            "name": "SmartSPD v2 API",
            "description": openapi_schema.get('info', {}).get('description', ''),
            "version": openapi_schema.get('info', {}).get('version', '1.0.0'),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{auth_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "auth_token",
                "value": "",
                "type": "string"
            }
        ],
        "item": [
            {
                "name": "Authentication",
                "item": [
                    {
                        "name": "Login",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "email": "agent@demo.com",
                                    "password": "demo123"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{base_url}}/api/v1/auth/login",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "auth", "login"]
                            }
                        }
                    },
                    {
                        "name": "Get Current User",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/api/v1/auth/me",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "auth", "me"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Documents",
                "item": [
                    {
                        "name": "Upload Document",
                        "request": {
                            "method": "POST",
                            "header": [],
                            "body": {
                                "mode": "formdata",
                                "formdata": [
                                    {
                                        "key": "file",
                                        "type": "file",
                                        "src": []
                                    },
                                    {
                                        "key": "document_type",
                                        "value": "spd",
                                        "type": "text"
                                    },
                                    {
                                        "key": "health_plan_id",
                                        "value": "plan_123",
                                        "type": "text"
                                    }
                                ]
                            },
                            "url": {
                                "raw": "{{base_url}}/api/v1/documents/upload",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "documents", "upload"]
                            }
                        }
                    },
                    {
                        "name": "List Documents",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/api/v1/documents/?skip=0&limit=10",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "documents", ""],
                                "query": [
                                    {
                                        "key": "skip",
                                        "value": "0"
                                    },
                                    {
                                        "key": "limit",
                                        "value": "10"
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Chat & AI",
                "item": [
                    {
                        "name": "Submit Query",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "query": "What is my deductible for medical services?",
                                    "health_plan_id": "plan_123"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{base_url}}/api/v1/chat/query",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "chat", "query"]
                            }
                        }
                    },
                    {
                        "name": "Get Conversations",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/api/v1/chat/conversations",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "chat", "conversations"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Analytics",
                "item": [
                    {
                        "name": "Dashboard Stats",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/api/v1/analytics/dashboard",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "analytics", "dashboard"]
                            }
                        }
                    },
                    {
                        "name": "Analytics Report",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/api/v1/analytics/report?days=30",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "analytics", "report"],
                                "query": [
                                    {
                                        "key": "days",
                                        "value": "30"
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    with open(docs_dir / "SmartSPD_v2_API.postman_collection.json", "w") as f:
        json.dump(collection, f, indent=2)

def generate_testing_guide(docs_dir: Path):
    """Generate API testing guide with examples"""
    
    testing_guide = """# SmartSPD v2 API Testing Guide

This guide provides comprehensive examples for testing the SmartSPD v2 API using various tools.

## Prerequisites

1. **Authentication Token**: Obtain a JWT token by logging in
2. **Base URL**: Use `http://localhost:8000` for development
3. **Test Data**: Sample documents and user accounts

## Authentication

### Login and Get Token
```bash
# Login request
curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "agent@demo.com",
    "password": "demo123"
  }'

# Response includes token
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {...}
}

# Set token for subsequent requests
export TOKEN="your-jwt-token-here"
```

## Document Management

### Upload Single Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "file=@sample_spd.pdf" \\
  -F "document_type=spd" \\
  -F "health_plan_id=plan_123"
```

### Upload Multiple Documents
```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch/upload" \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "files=@doc1.pdf" \\
  -F "files=@doc2.pdf" \\
  -F "document_type=spd" \\
  -F "health_plan_id=plan_123"
```

### Upload ZIP Archive
```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch/zip" \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "zip_file=@documents.zip" \\
  -F "health_plan_id=plan_123"
```

### Check Processing Status
```bash
curl -X GET "http://localhost:8000/api/v1/documents/batch/{batch_id}/status" \\
  -H "Authorization: Bearer $TOKEN"
```

### Download Document
```bash
curl -X GET "http://localhost:8000/api/v1/documents/{doc_id}/download" \\
  -H "Authorization: Bearer $TOKEN" \\
  -o downloaded_document.pdf
```

## AI Chat & Queries

### Submit Simple Query
```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "What is my deductible for medical services?",
    "health_plan_id": "plan_123"
  }'
```

### Submit Complex Query with Context
```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Compare my deductibles for in-network vs out-of-network providers",
    "health_plan_id": "plan_123",
    "conversation_id": "conv_456",
    "include_sources": true,
    "max_tokens": 500
  }'
```

### Get Query Suggestions
```bash
curl -X GET "http://localhost:8000/api/v1/chat/suggestions?health_plan_id=plan_123" \\
  -H "Authorization: Bearer $TOKEN"
```

### List Conversations
```bash
curl -X GET "http://localhost:8000/api/v1/chat/conversations?skip=0&limit=10" \\
  -H "Authorization: Bearer $TOKEN"
```

## Analytics & Reporting

### Dashboard Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard" \\
  -H "Authorization: Bearer $TOKEN"
```

### Comprehensive Analytics Report
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/report?days=30&include_trends=true" \\
  -H "Authorization: Bearer $TOKEN"
```

### Submit Query Feedback
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/feedback" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query_id": "query_123",
    "rating": 5,
    "feedback": "Very helpful and accurate response",
    "was_helpful": true
  }'
```

## User Management (Admin)

### List All Users
```bash
curl -X GET "http://localhost:8000/api/v1/admin/users?skip=0&limit=50" \\
  -H "Authorization: Bearer $TOKEN"
```

### Search Users
```bash
curl -X GET "http://localhost:8000/api/v1/admin/users?search=john&tpa_id=tpa_123" \\
  -H "Authorization: Bearer $TOKEN"
```

### Create New User
```bash
curl -X POST "http://localhost:8000/api/v1/admin/users" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "newuser@healthtpa.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "cs_agent",
    "tpa_id": "tpa_123",
    "password": "secure_password_123"
  }'
```

### Update User
```bash
curl -X PUT "http://localhost:8000/api/v1/admin/users/{user_id}" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "first_name": "Jane Updated",
    "role": "cs_manager",
    "is_active": true
  }'
```

### Reset User Password
```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/{user_id}/reset-password" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "new_password": "new_secure_password_456"
  }'
```

### Toggle User Status
```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/{user_id}/toggle-status" \\
  -H "Authorization: Bearer $TOKEN"
```

## User Activity Analytics

### User Activity Summary
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/summary/{user_id}?days=30" \\
  -H "Authorization: Bearer $TOKEN"
```

### TPA Activity Overview
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/tpa-overview?tpa_id=tpa_123&days=30" \\
  -H "Authorization: Bearer $TOKEN"
```

### Anomaly Detection
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/anomaly-detection/{user_id}?threshold=3.0" \\
  -H "Authorization: Bearer $TOKEN"
```

### Engagement Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/engagement-metrics?tpa_id=tpa_123&days=30" \\
  -H "Authorization: Bearer $TOKEN"
```

### Feature Usage Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/feature-usage?tpa_id=tpa_123&days=30" \\
  -H "Authorization: Bearer $TOKEN"
```

### Churn Risk Prediction
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/churn-risk/{user_id}" \\
  -H "Authorization: Bearer $TOKEN"
```

### Batch Churn Analysis
```bash
curl -X GET "http://localhost:8000/api/v1/user-activity/batch-churn-analysis?tpa_id=tpa_123&risk_threshold=medium" \\
  -H "Authorization: Bearer $TOKEN"
```

## Audit & Compliance

### View Audit Logs
```bash
curl -X GET "http://localhost:8000/api/v1/audit/logs?skip=0&limit=50&action=login" \\
  -H "Authorization: Bearer $TOKEN"
```

### Audit Summary
```bash
curl -X GET "http://localhost:8000/api/v1/audit/summary?days=7" \\
  -H "Authorization: Bearer $TOKEN"
```

### Export Audit Data
```bash
curl -X POST "http://localhost:8000/api/v1/audit/export" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "format": "csv",
    "filters": {
      "severity": ["medium", "high"],
      "resource_type": "user"
    }
  }'
```

## System Administration

### System Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/admin/stats" \\
  -H "Authorization: Bearer $TOKEN"
```

### System Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/admin/metrics" \\
  -H "Authorization: Bearer $TOKEN"
```

### Recent Activity
```bash
curl -X GET "http://localhost:8000/api/v1/admin/activity?limit=50&days=7" \\
  -H "Authorization: Bearer $TOKEN"
```

## TPA Management

### List TPAs
```bash
curl -X GET "http://localhost:8000/api/v1/admin/tpas?active_only=true" \\
  -H "Authorization: Bearer $TOKEN"
```

### Create TPA
```bash
curl -X POST "http://localhost:8000/api/v1/admin/tpas" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "New Health TPA",
    "slug": "new-health-tpa",
    "description": "A new third party administrator",
    "is_active": true
  }'
```

### Update TPA
```bash
curl -X PUT "http://localhost:8000/api/v1/admin/tpas/{tpa_id}" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Updated TPA Name",
    "description": "Updated description",
    "is_active": true
  }'
```

## Error Handling Examples

### Handle Validation Errors
```bash
# This will return a 422 validation error
curl -X POST "http://localhost:8000/api/v1/chat/query" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "",
    "health_plan_id": "invalid_id"
  }'

# Response:
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "type": "validation_error",
  "details": {
    "query": "Query cannot be empty",
    "health_plan_id": "Invalid health plan ID format"
  }
}
```

### Handle Rate Limits
```bash
# After exceeding rate limits, you'll get:
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests",
  "type": "rate_limit_error",
  "retry_after": 60
}
```

## Testing Scenarios

### End-to-End Document Processing
1. Login and get token
2. Upload document
3. Check processing status
4. Query the document content
5. Download the processed document

### User Management Workflow
1. Login as admin
2. Create new user
3. Update user details
4. Check user activity
5. Reset user password
6. Toggle user status

### Analytics Workflow
1. Login as manager
2. Get dashboard statistics
3. Generate detailed report
4. Analyze user engagement
5. Check feature usage
6. Export data

## Performance Testing

### Load Testing with Apache Bench
```bash
# Test login endpoint
ab -n 100 -c 10 -H "Content-Type: application/json" \\
  -p login_data.json \\
  http://localhost:8000/api/v1/auth/login

# Test query endpoint (with auth)
ab -n 50 -c 5 -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -p query_data.json \\
  http://localhost:8000/api/v1/chat/query
```

### Monitoring Endpoints
```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Application health
curl -X GET "http://localhost:8000/api/v1/health"
```

## Troubleshooting

### Common Issues
1. **401 Unauthorized**: Check token validity and format
2. **403 Forbidden**: Verify user role and permissions
3. **422 Validation Error**: Check request body format
4. **429 Rate Limited**: Wait and retry with backoff
5. **503 Service Unavailable**: AI service may be down

### Debug Mode
Add `?debug=true` to any endpoint for detailed error information (development only).

---
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(docs_dir / "TESTING_GUIDE.md", "w") as f:
        f.write(testing_guide)

def generate_api_reference(docs_dir: Path):
    """Generate detailed API reference"""
    
    openapi_schema = custom_openapi(app)
    
    # Create an index.html file
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartSPD v2 API Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f2937;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .nav {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .nav a {{
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }}
        .nav a:hover {{
            background: #5a67d8;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #667eea;
            background: #f8fafc;
        }}
        code {{
            background: #e2e8f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .stat h3 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .stat p {{
            margin: 0;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 SmartSPD v2 API Documentation</h1>
        
        <p><strong>Version:</strong> {openapi_schema.get('info', {}).get('version', '1.0.0')}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <div class="stat">
                <h3>{len(openapi_schema.get('paths', {}))}</h3>
                <p>API Endpoints</p>
            </div>
            <div class="stat">
                <h3>{len(openapi_schema.get('components', {}).get('schemas', {}))}</h3>
                <p>Data Schemas</p>
            </div>
            <div class="stat">
                <h3>{len(openapi_schema.get('tags', []))}</h3>
                <p>API Categories</p>
            </div>
        </div>

        <div class="nav">
            <h3>📋 Available Documentation</h3>
            <a href="openapi.json" target="_blank">🔧 OpenAPI Specification</a>
            <a href="README.md" target="_blank">📖 API Reference</a>
            <a href="TESTING_GUIDE.md" target="_blank">🧪 Testing Guide</a>
            <a href="SmartSPD_v2_API.postman_collection.json" target="_blank">📮 Postman Collection</a>
            <a href="http://localhost:8000/api/docs" target="_blank">🌐 Interactive Docs</a>
        </div>

        <div class="section">
            <h2>🏗️ Architecture Overview</h2>
            <p>SmartSPD v2 is an enterprise-grade AI-powered health plan assistant built with:</p>
            <ul>
                <li><strong>FastAPI</strong> - High-performance async Python web framework</li>
                <li><strong>PostgreSQL</strong> - Multi-tenant database with row-level security</li>
                <li><strong>Redis</strong> - Caching and session management</li>
                <li><strong>Pinecone</strong> - Vector database for semantic search</li>
                <li><strong>OpenAI</strong> - Large language model integration</li>
                <li><strong>Auth0</strong> - Enterprise authentication and authorization</li>
            </ul>
        </div>

        <div class="section">
            <h2>🔐 Authentication</h2>
            <p>All API endpoints require JWT Bearer token authentication:</p>
            <code>Authorization: Bearer &lt;your-jwt-token&gt;</code>
            <p>Obtain tokens through the <code>/api/v1/auth/login</code> endpoint.</p>
        </div>

        <div class="section">
            <h2>⚡ Quick Start</h2>
            <ol>
                <li>Start the development server: <code>./start_development.sh</code></li>
                <li>Login to get a token: <code>POST /api/v1/auth/login</code></li>
                <li>Upload a document: <code>POST /api/v1/documents/upload</code></li>
                <li>Query the document: <code>POST /api/v1/chat/query</code></li>
                <li>View analytics: <code>GET /api/v1/analytics/dashboard</code></li>
            </ol>
        </div>

        <div class="section">
            <h2>📊 API Categories</h2>
            <ul>"""

    # Add API tags
    for tag in openapi_schema.get('tags', []):
        index_html += f"""
                <li><strong>{tag['name'].title()}</strong> - {tag.get('description', '')}</li>"""

    index_html += f"""
            </ul>
        </div>

        <div class="section">
            <h2>🔗 Related Resources</h2>
            <ul>
                <li><a href="http://localhost:8000/api/docs" target="_blank">Interactive API Documentation (Swagger UI)</a></li>
                <li><a href="http://localhost:8000/api/redoc" target="_blank">Alternative Documentation (ReDoc)</a></li>
                <li><a href="https://github.com/smartspd/api" target="_blank">GitHub Repository</a></li>
                <li><a href="https://docs.smartspd.com" target="_blank">Full Documentation</a></li>
            </ul>
        </div>

        <div class="section">
            <h2>🆘 Support</h2>
            <p>Need help? Contact us:</p>
            <ul>
                <li><strong>Email:</strong> api-support@smartspd.com</li>
                <li><strong>GitHub Issues:</strong> <a href="https://github.com/smartspd/api/issues">Report a Bug</a></li>
                <li><strong>Documentation:</strong> <a href="https://docs.smartspd.com">Complete Guide</a></li>
            </ul>
        </div>

        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #6b7280;">
            <p>Generated with ❤️ by SmartSPD v2 API Documentation Generator</p>
        </footer>
    </div>
</body>
</html>"""
    
    with open(docs_dir / "index.html", "w") as f:
        f.write(index_html)

if __name__ == "__main__":
    generate_documentation()