# SmartSPD v2 API Documentation

## Overview

SmartSPD v2 is an enterprise-grade AI-powered health plan assistant designed for Third Party Administrator (TPA) customer service operations. The API provides comprehensive functionality for document management, AI-powered chat queries, user administration, analytics, and compliance tracking.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.smartspd.com`

## Authentication

SmartSPD uses JWT-based authentication with role-based access control (RBAC).

### Authentication Flow

1. **Login** - Exchange credentials for JWT tokens
2. **Authorization** - Include JWT token in request headers
3. **Token Refresh** - Refresh tokens before expiration

### Headers

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### User Roles

- **tpa_admin**: Full system administration access
- **cs_manager**: Manager-level access within TPA
- **cs_agent**: Agent-level access for customer service
- **member**: Limited access for health plan members
- **readonly**: Read-only access to documents and plans

## Multi-Tenant Architecture

SmartSPD operates in a multi-tenant environment where each TPA has isolated data access. All API operations are automatically scoped to the user's TPA unless explicitly specified for admin operations.

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Authentication**: 5 requests per minute per IP
- **General API**: 10 requests per second per user
- **Upload Operations**: 3 concurrent uploads per user

## Error Handling

### Standard Error Response

```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "type": "error_category",
  "details": {
    "field": "Additional context"
  }
}
```

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **429**: Rate Limited
- **500**: Internal Server Error
- **503**: Service Unavailable

## API Endpoints

### Authentication (`/api/v1/auth`)

#### POST `/api/v1/auth/login`
Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "role": "cs_agent",
    "tpa_id": "tpa_456"
  }
}
```

#### POST `/api/v1/auth/refresh`
Refresh JWT access token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST `/api/v1/auth/logout`
Invalidate current session.

### Document Management (`/api/v1/documents`)

#### POST `/api/v1/documents/upload`
Upload a single document for processing.

**Parameters:**
- `file`: File (multipart/form-data)
- `health_plan_id`: string (optional)
- `document_type`: enum["spd", "bps", "other"] (optional)
- `metadata`: JSON object (optional)

**Response:**
```json
{
  "id": "doc_123",
  "filename": "health_plan_spd.pdf",
  "document_type": "spd",
  "file_size": 2048576,
  "processing_status": "processing",
  "upload_progress": 100,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### POST `/api/v1/documents/batch/upload`
Upload multiple documents simultaneously.

**Parameters:**
- `files`: Array of files (multipart/form-data)
- `health_plan_id`: string (optional)
- `batch_notes`: string (optional)

**Response:**
```json
{
  "batch_id": "batch_456",
  "uploaded_documents": [
    {
      "id": "doc_123",
      "filename": "document1.pdf",
      "status": "uploaded"
    }
  ],
  "failed_uploads": [],
  "total_files": 3
}
```

#### GET `/api/v1/documents/{document_id}`
Retrieve document details and processing status.

#### GET `/api/v1/documents/{document_id}/versions`
Get document version history.

#### POST `/api/v1/documents/{document_id}/versions/upload`
Upload a new version of an existing document.

### Chat & Queries (`/api/v1/chat`)

#### POST `/api/v1/chat/query`
Submit an AI-powered query about health plan benefits.

**Request:**
```json
{
  "query": "What is the deductible for emergency room visits?",
  "health_plan_id": "plan_789",
  "conversation_id": "conv_123",
  "context": {
    "member_id": "member_456",
    "plan_year": 2024
  }
}
```

**Response:**
```json
{
  "query_id": "query_789",
  "response": "The emergency room deductible for your plan is $500 per visit...",
  "confidence_score": 0.92,
  "sources": [
    {
      "document_id": "doc_123",
      "document_name": "Health Plan SPD 2024",
      "page_number": 15,
      "chunk_text": "Emergency services are subject to..."
    }
  ],
  "health_plan_id": "plan_789",
  "conversation_id": "conv_123",
  "response_time_ms": 1250
}
```

#### GET `/api/v1/chat/conversations`
Retrieve user's conversation history.

#### GET `/api/v1/chat/suggestions`
Get suggested queries based on user context.

### Analytics (`/api/v1/analytics`)

#### GET `/api/v1/analytics/dashboard`
Get real-time dashboard analytics.

**Response:**
```json
{
  "active_users_today": 127,
  "queries_today": 1834,
  "documents_processed": 45,
  "avg_response_time": 1.23,
  "top_queries": [
    {
      "query": "deductible information",
      "count": 89
    }
  ],
  "user_satisfaction": 4.2
}
```

#### GET `/api/v1/analytics/report`
Generate comprehensive analytics report.

**Parameters:**
- `start_date`: ISO date string
- `end_date`: ISO date string  
- `tpa_id`: string (admin only)

#### POST `/api/v1/analytics/feedback`
Submit user feedback on query responses.

### Administration (`/api/v1/admin`)

*Requires admin role*

#### GET `/api/v1/admin/stats`
Get system-wide statistics.

#### GET `/api/v1/admin/users`
Manage user accounts.

**Parameters:**
- `search`: string (optional)
- `tpa_id`: string (optional)
- `is_active`: boolean (optional)
- `skip`: integer (default: 0)
- `limit`: integer (default: 100)

#### POST `/api/v1/admin/users`
Create new user account.

#### PUT `/api/v1/admin/users/{user_id}`
Update user account.

#### DELETE `/api/v1/admin/users/{user_id}`
Delete user account.

#### POST `/api/v1/admin/users/{user_id}/reset-password`
Reset user password.

#### GET `/api/v1/admin/tpas`
Manage TPA organizations.

#### POST `/api/v1/admin/tpas`
Create new TPA.

### Audit Trail (`/api/v1/audit`)

*Requires manager+ role*

#### GET `/api/v1/audit/logs`
Retrieve audit logs with filtering.

**Parameters:**
- `user_id`: string (optional)
- `action`: string (optional)
- `resource_type`: string (optional)
- `severity`: enum["low", "medium", "high", "critical"] (optional)
- `start_date`: ISO date string (optional)
- `end_date`: ISO date string (optional)
- `success`: boolean (optional)

#### GET `/api/v1/audit/summary`
Get audit statistics summary.

#### GET `/api/v1/audit/security`
Get security-related audit events (admin only).

### User Activity (`/api/v1/user-activity`)

*Requires manager+ role*

#### GET `/api/v1/user-activity/summary/{user_id}`
Get comprehensive user activity summary.

#### GET `/api/v1/user-activity/tpa-overview`
Get TPA-wide activity overview.

#### GET `/api/v1/user-activity/anomaly-detection/{user_id}`
Detect unusual activity patterns.

#### GET `/api/v1/user-activity/engagement-metrics`
Get user engagement analytics.

#### GET `/api/v1/user-activity/insights`
Get AI-generated activity insights and recommendations.

## Data Models

### User
```json
{
  "id": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "enum",
  "tpa_id": "string",
  "is_active": "boolean",
  "last_login_at": "datetime",
  "created_at": "datetime"
}
```

### Document
```json
{
  "id": "string",
  "filename": "string",
  "document_type": "enum",
  "file_size": "integer",
  "file_hash": "string",
  "processing_status": "enum",
  "health_plan_id": "string",
  "uploaded_by": "string",
  "tpa_id": "string",
  "metadata": "object",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Chat Query
```json
{
  "id": "string",
  "query": "string",
  "response": "string",
  "confidence_score": "float",
  "sources": "array",
  "user_id": "string",
  "health_plan_id": "string",
  "conversation_id": "string",
  "response_time_ms": "integer",
  "created_at": "datetime"
}
```

### Audit Log
```json
{
  "id": "string",
  "user_id": "string",
  "action": "string",
  "resource_type": "string",
  "resource_id": "string",
  "description": "string",
  "severity": "enum",
  "success": "boolean",
  "ip_address": "string",
  "user_agent": "string",
  "metadata": "object",
  "created_at": "datetime"
}
```

## WebSocket Connections

### Real-time Updates (`/ws/updates`)

Connect to receive real-time updates for:
- Document processing status
- New chat messages
- System notifications
- Analytics updates

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates?token=jwt_token');
```

**Message Format:**
```json
{
  "type": "document_processed",
  "data": {
    "document_id": "doc_123",
    "status": "completed"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## SDKs and Client Libraries

### JavaScript/TypeScript
```bash
npm install @smartspd/api-client
```

```javascript
import { SmartSPDClient } from '@smartspd/api-client';

const client = new SmartSPDClient({
  baseURL: 'https://api.smartspd.com',
  apiKey: 'your-api-key'
});

// Submit a query
const response = await client.chat.query({
  query: "What is my deductible?",
  healthPlanId: "plan_123"
});
```

### Python
```bash
pip install smartspd-client
```

```python
from smartspd_client import SmartSPDClient

client = SmartSPDClient(
    base_url="https://api.smartspd.com",
    api_key="your-api-key"
)

# Upload document
document = client.documents.upload(
    file_path="health_plan.pdf",
    document_type="spd"
)
```

## Webhooks

SmartSPD can send webhook notifications for important events:

### Webhook Events
- `document.processed` - Document processing completed
- `document.failed` - Document processing failed
- `user.created` - New user account created
- `query.completed` - Chat query processed
- `audit.security_event` - Security event detected

### Webhook Payload
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

## Testing

### API Testing

Use the interactive API documentation at `/api/docs` for testing endpoints.

### Sample Requests

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Upload document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "document_type=spd"

# Submit query
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my deductible?", "health_plan_id": "plan_123"}'
```

## Performance Guidelines

### Optimization Tips

1. **Pagination**: Use `skip` and `limit` parameters for large datasets
2. **Filtering**: Apply filters to reduce response size
3. **Caching**: Leverage ETags and cache headers
4. **Batch Operations**: Use batch endpoints for multiple operations
5. **Compression**: Enable gzip compression for responses

### Resource Limits

- **File Upload**: Maximum 10MB per file
- **Batch Upload**: Maximum 20 files per batch
- **Query Length**: Maximum 1000 characters
- **Response Size**: Maximum 5MB per response

## Support and Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check JWT token validity and format
2. **403 Forbidden**: Verify user role permissions
3. **422 Validation Error**: Check request body format and required fields
4. **503 Service Unavailable**: AI services may be temporarily unavailable

### Debug Headers

Include these headers for debugging:
- `X-Request-ID`: Unique request identifier
- `X-Debug-Mode`: Enable verbose error messages (development only)

### Contact Support

- **Email**: support@smartspd.com
- **Documentation**: https://docs.smartspd.com
- **Status Page**: https://status.smartspd.com

## Changelog

### v2.1.0 (Latest)
- Added user activity tracking endpoints
- Enhanced audit logging capabilities
- Improved document version control
- Added batch processing for documents

### v2.0.0
- Complete API redesign
- Multi-tenant architecture
- Enhanced security with RBAC
- Real-time analytics dashboard

### v1.x
- Legacy API (deprecated)

---

*This documentation is automatically generated from OpenAPI specifications and kept up-to-date with the latest API changes.*