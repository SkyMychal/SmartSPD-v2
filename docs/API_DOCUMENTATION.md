# SmartSPD v2 API Documentation

**Version:** 2.0.0  
**Generated:** 2024-01-15 10:30:00

## Overview

SmartSPD v2 is an enterprise-grade AI-powered health plan assistant for TPA (Third Party Administrator) customer service operations. It enables agents to provide instant, accurate answers to health plan member questions using advanced RAG (Retrieval-Augmented Generation) technology.

## Base URLs
- **Development**: `http://localhost:8000`
- **Production**: `https://api.smartspd.com`

## Authentication

All API endpoints require JWT Bearer token authentication.

```bash
Authorization: Bearer <your-jwt-token>
```

### Get Authentication Token
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "agent@demo.com",
  "password": "demo123"
}
```

## API Endpoints

### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | User login |
| `POST` | `/api/v1/auth/logout` | User logout |
| `GET` | `/api/v1/auth/me` | Get current user info |

### 👥 Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users/` | List users |
| `POST` | `/api/v1/users/` | Create user |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PUT` | `/api/v1/users/{id}` | Update user |
| `DELETE` | `/api/v1/users/{id}` | Delete user |

### 📄 Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload single document |
| `POST` | `/api/v1/documents/batch/upload` | Upload multiple documents |
| `POST` | `/api/v1/documents/batch/zip` | Upload ZIP archive |
| `GET` | `/api/v1/documents/{id}` | Get document details |
| `GET` | `/api/v1/documents/{id}/download` | Download document |
| `POST` | `/api/v1/documents/{id}/versions/upload` | Upload new version |
| `GET` | `/api/v1/documents/{id}/versions` | Get version history |
| `GET` | `/api/v1/documents/batch/{id}/status` | Check batch processing status |

### 💬 Chat & AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat/query` | Submit AI query |
| `GET` | `/api/v1/chat/conversations` | List conversations |
| `GET` | `/api/v1/chat/suggestions` | Get query suggestions |

### 📊 Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/dashboard` | Dashboard statistics |
| `GET` | `/api/v1/analytics/report` | Comprehensive analytics |
| `POST` | `/api/v1/analytics/feedback` | Submit query feedback |

### 🔧 Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/stats` | System statistics |
| `GET` | `/api/v1/admin/metrics` | System metrics |
| `GET` | `/api/v1/admin/activity` | Recent activity |
| `GET` | `/api/v1/admin/users` | User management with filters |
| `POST` | `/api/v1/admin/users` | Create new user |
| `PUT` | `/api/v1/admin/users/{id}` | Update user |
| `DELETE` | `/api/v1/admin/users/{id}` | Delete user |
| `POST` | `/api/v1/admin/users/{id}/reset-password` | Reset password |
| `POST` | `/api/v1/admin/users/{id}/toggle-status` | Toggle user status |
| `GET` | `/api/v1/admin/tpas` | TPA management |
| `POST` | `/api/v1/admin/tpas` | Create TPA |
| `PUT` | `/api/v1/admin/tpas/{id}` | Update TPA |
| `DELETE` | `/api/v1/admin/tpas/{id}` | Delete TPA |

### 📋 Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/audit/logs` | View audit logs |
| `GET` | `/api/v1/audit/summary` | Audit summary |
| `POST` | `/api/v1/audit/export` | Export audit data |
| `GET` | `/api/v1/audit/filters` | Get filter options |

### 👤 User Activity
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/user-activity/summary/{user_id}` | User activity summary |
| `GET` | `/api/v1/user-activity/tpa-overview` | TPA activity overview |
| `GET` | `/api/v1/user-activity/anomaly-detection/{user_id}` | Anomaly detection |
| `GET` | `/api/v1/user-activity/engagement-metrics` | Engagement metrics |
| `GET` | `/api/v1/user-activity/feature-usage` | Feature usage analytics |
| `GET` | `/api/v1/user-activity/insights` | Activity insights |
| `GET` | `/api/v1/user-activity/daily-patterns/{user_id}` | Daily patterns |
| `POST` | `/api/v1/user-activity/track-session` | Track user session |
| `GET` | `/api/v1/user-activity/inactive-users` | Get inactive users |
| `GET` | `/api/v1/user-activity/churn-risk/{user_id}` | Churn risk prediction |
| `GET` | `/api/v1/user-activity/user-journey/{user_id}` | User journey analytics |
| `GET` | `/api/v1/user-activity/real-time-activity` | Real-time monitoring |
| `GET` | `/api/v1/user-activity/batch-churn-analysis` | Batch churn analysis |

### 🏢 TPAs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tpas/me` | Get current user's TPA |

### 🏥 Health Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health-plans/` | List health plans |

## Request/Response Examples

### Login Request
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "agent@demo.com",
    "password": "demo123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "email": "agent@demo.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "cs_agent",
    "tpa_id": "tpa_456"
  }
}
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_spd.pdf" \
  -F "document_type=spd" \
  -F "health_plan_id=plan_123"
```

**Response:**
```json
{
  "id": "doc_789",
  "filename": "sample_spd.pdf",
  "document_type": "spd",
  "file_size": 2048576,
  "processing_status": "pending",
  "health_plan_id": "plan_123",
  "uploaded_by": "user_123",
  "created_at": "2024-01-15T09:00:00Z"
}
```

### Submit AI Query
```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is my deductible for medical services?",
    "health_plan_id": "plan_123"
  }'
```

**Response:**
```json
{
  "id": "query_456",
  "response": "Your deductible for medical services is $1,000 per calendar year for in-network providers and $2,000 for out-of-network providers.",
  "confidence_score": 0.95,
  "sources": [
    {
      "document_id": "doc_789",
      "chunk_id": "chunk_123",
      "relevance_score": 0.92
    }
  ],
  "response_time_ms": 1200,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get Dashboard Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total_documents": 145,
  "total_queries": 2340,
  "active_users": 89,
  "avg_response_time": 1.2,
  "success_rate": 0.97,
  "recent_activity": {
    "queries_today": 156,
    "documents_uploaded_today": 12,
    "active_users_today": 45
  },
  "trends": {
    "queries_7d": [120, 145, 134, 189, 167, 145, 156],
    "success_rate_7d": [0.96, 0.97, 0.95, 0.98, 0.97, 0.96, 0.97]
  }
}
```

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "type": "error_code",
  "details": {}
}
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

### Example Error Responses

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token",
  "type": "authentication_error"
}
```

**422 Validation Error:**
```json
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

**429 Rate Limit:**
```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests",
  "type": "rate_limit_error",
  "retry_after": 60
}
```

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

**Response format:**
```json
{
  "items": [...],
  "meta": {
    "total": 150,
    "skip": 0,
    "limit": 50,
    "has_next": true
  }
}
```

## Data Models

### User Roles
- `tpa_admin` - Full system access
- `cs_manager` - TPA management and analytics
- `cs_agent` - Basic query and document access
- `member` - Read-only member access
- `readonly` - View-only access

### Document Types
- `spd` - Summary Plan Description
- `bps` - Benefit Plan Specification
- `certificate` - Certificate of Coverage
- `amendment` - Plan Amendment
- `other` - Other document types

### Processing Status
- `pending` - Awaiting processing
- `processing` - Currently being processed
- `completed` - Processing completed successfully
- `failed` - Processing failed

### Audit Severity Levels
- `low` - Informational events
- `medium` - Important events
- `high` - Security-relevant events
- `critical` - Critical security events

## Webhooks

SmartSPD supports webhooks for event notifications:

### Document Processing Events
```json
{
  "event": "document.processed",
  "data": {
    "document_id": "doc_123",
    "status": "completed",
    "processing_time_ms": 5000
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "signature": "sha256=..."
}
```

### Query Completion Events
```json
{
  "event": "query.completed",
  "data": {
    "query_id": "query_456",
    "user_id": "user_123",
    "confidence_score": 0.95,
    "response_time_ms": 1200
  },
  "timestamp": "2024-01-15T10:30:05Z",
  "signature": "sha256=..."
}
```

## Security

### Multi-Tenant Architecture
- All data is isolated by TPA ID
- Row-level security in database
- API endpoints enforce TPA boundaries

### Data Protection
- HIPAA compliance for health data
- Complete audit logging
- Encrypted data transmission
- Secure file storage

### Rate Limiting
- Per-user and per-TPA limits
- Adaptive rate limiting based on usage patterns
- Protection against abuse

## Interactive Documentation

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

## SDKs and Tools

### Python SDK
```bash
pip install smartspd-client
```

```python
from smartspd_client import SmartSPDClient

client = SmartSPDClient(
    base_url="http://localhost:8000",
    token="your-jwt-token"
)

# Upload document
document = client.documents.upload(
    file_path="health_plan.pdf",
    document_type="spd",
    health_plan_id="plan_123"
)

# Submit query
response = client.chat.query(
    query="What is my deductible?",
    health_plan_id="plan_123"
)
```

### cURL Examples
See the testing guide for comprehensive cURL examples.

### Postman Collection
Import the provided Postman collection for easy API testing.

## Support

- **Documentation**: [SmartSPD Docs](https://docs.smartspd.com)
- **API Issues**: [GitHub Issues](https://github.com/smartspd/api/issues)
- **Email Support**: api-support@smartspd.com

## Changelog

### v2.0.0 (2024-01-15)
- Complete rewrite with FastAPI
- Enhanced security and multi-tenancy
- Advanced analytics and user activity tracking
- Comprehensive audit logging
- Real-time features and WebSocket support
- Improved AI capabilities with RAG

### v1.5.0 (2023-12-01)
- Added batch document processing
- Enhanced search capabilities
- Performance improvements

### v1.0.0 (2023-10-01)
- Initial release
- Basic document upload and query functionality
- User management and authentication

---
*Last updated: 2024-01-15 10:30:00*