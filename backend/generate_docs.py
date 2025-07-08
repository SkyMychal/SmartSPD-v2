#!/usr/bin/env python3
"""
Generate comprehensive API documentation for SmartSPD v2

This script generates:
1. OpenAPI JSON specification
2. Markdown documentation
3. Postman collection
4. HTML documentation
"""
import json
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.core.openapi import custom_openapi, generate_openapi_json
from app.core.config import settings


def generate_markdown_docs(openapi_schema: dict) -> str:
    """Generate comprehensive Markdown documentation"""
    
    md_content = f"""# {openapi_schema['info']['title']} API Documentation

Version: {openapi_schema['info']['version']}

{openapi_schema['info']['description']}

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.smartspd.com`

## Authentication

This API uses Bearer token authentication. Include your JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

To obtain a token, use the login endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{{"email": "your-email@domain.com", "password": "your-password"}}'
```

## API Endpoints

"""
    
    # Group endpoints by tags
    endpoints_by_tag = {}
    
    for path, methods in openapi_schema.get('paths', {}).items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                tags = details.get('tags', ['Untagged'])
                tag = tags[0] if tags else 'Untagged'
                
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                
                endpoints_by_tag[tag].append({
                    'path': path,
                    'method': method.upper(),
                    'summary': details.get('summary', ''),
                    'description': details.get('description', ''),
                    'parameters': details.get('parameters', []),
                    'requestBody': details.get('requestBody'),
                    'responses': details.get('responses', {})
                })
    
    # Generate documentation for each tag
    for tag, endpoints in endpoints_by_tag.items():
        md_content += f"### {tag.title()}\n\n"
        
        for endpoint in endpoints:
            md_content += f"#### {endpoint['method']} {endpoint['path']}\n\n"
            
            if endpoint['summary']:
                md_content += f"**{endpoint['summary']}**\n\n"
            
            if endpoint['description']:
                md_content += f"{endpoint['description']}\n\n"
            
            # Parameters
            if endpoint['parameters']:
                md_content += "**Parameters:**\n\n"
                md_content += "| Name | Type | Required | Description |\n"
                md_content += "|------|------|----------|-------------|\n"
                
                for param in endpoint['parameters']:
                    name = param.get('name', '')
                    param_type = param.get('schema', {}).get('type', param.get('type', ''))
                    required = 'Yes' if param.get('required', False) else 'No'
                    description = param.get('description', '')
                    md_content += f"| {name} | {param_type} | {required} | {description} |\n"
                
                md_content += "\n"
            
            # Request body
            if endpoint['requestBody']:
                md_content += "**Request Body:**\n\n"
                content = endpoint['requestBody'].get('content', {})
                for content_type, schema_info in content.items():
                    md_content += f"Content-Type: `{content_type}`\n\n"
                    if 'example' in schema_info:
                        md_content += "```json\n"
                        md_content += json.dumps(schema_info['example'], indent=2)
                        md_content += "\n```\n\n"
            
            # Responses
            md_content += "**Responses:**\n\n"
            for status_code, response in endpoint['responses'].items():
                description = response.get('description', '')
                md_content += f"- **{status_code}**: {description}\n"
            
            md_content += "\n---\n\n"
    
    # Add error handling section
    md_content += """## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

### Standard Error Response

```json
{
  "error": "Error Type",
  "message": "Detailed error description", 
  "type": "error_category",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **429**: Rate Limit Exceeded
- **500**: Internal Server Error

## Rate Limiting

API requests are rate-limited based on your subscription:

- **Basic**: 100 requests/minute
- **Professional**: 500 requests/minute
- **Enterprise**: 2000 requests/minute

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 499
X-RateLimit-Reset: 1640995200
```

## SDKs and Client Libraries

### Python

```bash
pip install smartspd-client
```

```python
from smartspd_client import SmartSPDClient

client = SmartSPDClient(
    api_key="your-api-key",
    base_url="https://api.smartspd.com"
)

# Submit a query
response = client.chat.query(
    query="What is my deductible?",
    health_plan_id="plan-123"
)
```

### JavaScript/Node.js

```bash
npm install @smartspd/client
```

```javascript
import { SmartSPDClient } from '@smartspd/client';

const client = new SmartSPDClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.smartspd.com'
});

// Submit a query
const response = await client.chat.query({
  query: 'What is my deductible?',
  healthPlanId: 'plan-123'
});
```

## Webhooks

SmartSPD supports webhooks for real-time notifications:

### Document Processing Webhook

```json
{
  "event": "document.processed",
  "data": {
    "document_id": "doc_123",
    "status": "completed",
    "processing_time_ms": 15000
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "signature": "sha256=abc123..."
}
```

### Query Completion Webhook

```json
{
  "event": "query.completed", 
  "data": {
    "query_id": "query_456",
    "user_id": "user_789",
    "confidence_score": 0.92,
    "response_time_ms": 1200
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "signature": "sha256=def456..."
}
```

## Support

- **Documentation**: https://docs.smartspd.com
- **Support Email**: support@smartspd.com
- **Status Page**: https://status.smartspd.com
- **GitHub Issues**: https://github.com/smartspd/api-issues
"""
    
    return md_content


def generate_postman_collection(openapi_schema: dict) -> dict:
    """Generate Postman collection from OpenAPI schema"""
    
    collection = {
        "info": {
            "name": openapi_schema['info']['title'],
            "description": openapi_schema['info']['description'],
            "version": openapi_schema['info']['version'],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{jwt_token}}",
                    "type": "string"
                }
            ]
        },
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Auto-refresh token if needed",
                        "if (!pm.globals.get('jwt_token') || pm.globals.get('token_expires') < Date.now()) {",
                        "    // Add token refresh logic here",
                        "}"
                    ]
                }
            }
        ],
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "jwt_token", 
                "value": "",
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Group endpoints by tags for folders
    folders = {}
    
    for path, methods in openapi_schema.get('paths', {}).items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                tags = details.get('tags', ['Untagged'])
                tag = tags[0] if tags else 'Untagged'
                
                if tag not in folders:
                    folders[tag] = {
                        "name": tag.title(),
                        "description": f"Endpoints related to {tag}",
                        "item": []
                    }
                
                # Create request item
                request_item = {
                    "name": details.get('summary', f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "url": {
                            "raw": "{{base_url}}" + path,
                            "host": ["{{base_url}}"],
                            "path": path.strip('/').split('/')
                        },
                        "description": details.get('description', '')
                    }
                }
                
                # Add query parameters
                if details.get('parameters'):
                    query_params = []
                    for param in details['parameters']:
                        if param.get('in') == 'query':
                            query_params.append({
                                "key": param.get('name'),
                                "value": param.get('example', ''),
                                "description": param.get('description', '')
                            })
                    if query_params:
                        request_item["request"]["url"]["query"] = query_params
                
                # Add request body for POST/PUT
                if method.upper() in ['POST', 'PUT', 'PATCH'] and details.get('requestBody'):
                    content = details['requestBody'].get('content', {})
                    if 'application/json' in content:
                        example = content['application/json'].get('example', {})
                        request_item["request"]["body"] = {
                            "mode": "raw",
                            "raw": json.dumps(example, indent=2),
                            "options": {
                                "raw": {
                                    "language": "json"
                                }
                            }
                        }
                
                folders[tag]["item"].append(request_item)
    
    # Add folders to collection
    collection["item"] = list(folders.values())
    
    return collection


def main():
    """Generate all documentation files"""
    
    print("Generating SmartSPD v2 API Documentation...")
    
    # Create docs directory
    docs_dir = project_root / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI schema
    print("1. Generating OpenAPI schema...")
    openapi_schema = custom_openapi(app)
    
    # Save OpenAPI JSON
    openapi_file = docs_dir / "openapi.json"
    with open(openapi_file, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"   ✓ OpenAPI spec saved to {openapi_file}")
    
    # Generate Markdown documentation
    print("2. Generating Markdown documentation...")
    markdown_content = generate_markdown_docs(openapi_schema)
    markdown_file = docs_dir / "README.md"
    with open(markdown_file, 'w') as f:
        f.write(markdown_content)
    print(f"   ✓ Markdown docs saved to {markdown_file}")
    
    # Generate Postman collection
    print("3. Generating Postman collection...")
    postman_collection = generate_postman_collection(openapi_schema)
    postman_file = docs_dir / "smartspd-postman-collection.json"
    with open(postman_file, 'w') as f:
        json.dump(postman_collection, f, indent=2)
    print(f"   ✓ Postman collection saved to {postman_file}")
    
    # Generate API reference HTML
    print("4. Generating HTML documentation...")
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{openapi_schema['info']['title']} API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        .swagger-ui .topbar {{ display: none; }}
        .swagger-ui .info {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script>
        const ui = SwaggerUIBundle({{
            url: './openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout"
        }});
    </script>
</body>
</html>"""
    
    html_file = docs_dir / "index.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    print(f"   ✓ HTML docs saved to {html_file}")
    
    print("\n📚 Documentation generation complete!")
    print(f"\nGenerated files in {docs_dir}:")
    print("   - openapi.json (OpenAPI 3.0 specification)")
    print("   - README.md (Comprehensive Markdown documentation)")
    print("   - smartspd-postman-collection.json (Postman collection)")
    print("   - index.html (Interactive HTML documentation)")
    
    print(f"\n🌐 To view the documentation:")
    print(f"   - Markdown: Open {markdown_file}")
    print(f"   - HTML: Open {html_file} in a web browser")
    print(f"   - Postman: Import {postman_file} into Postman")
    
    print(f"\n🚀 API Server Documentation:")
    print("   - Swagger UI: http://localhost:8000/api/docs")
    print("   - ReDoc: http://localhost:8000/api/redoc")
    print("   - OpenAPI JSON: http://localhost:8000/api/openapi.json")


if __name__ == "__main__":
    main()