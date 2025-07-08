# SmartSPD v2 Backend

FastAPI-based backend for the SmartSPD AI-powered health plan assistant.

## 🚀 Quick Start

```bash
# From project root
./start_development.sh
```

## 🏗️ Architecture

### Tech Stack
- **FastAPI** - Modern, fast Python web framework
- **PostgreSQL** - Multi-tenant database with JSONB support
- **Redis** - Session management and caching
- **Neo4j** - Knowledge graph for benefit relationships
- **Pinecone** - Vector database for semantic search
- **OpenAI** - AI-powered responses and embeddings

### Project Structure
```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Core functionality
│   ├── crud/             # Database operations
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application
├── migrations/           # Database migrations
├── requirements.txt      # Python dependencies
└── Dockerfile           # Container configuration
```

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL, Redis, Neo4j (via Docker)

### Environment Setup
1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your API keys:
   - OpenAI API Key
   - Pinecone API Key
   - Auth0 credentials

3. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup
```bash
# Start infrastructure
docker-compose up -d postgres redis neo4j

# Run migrations
python -c "from app.core.database import create_tables; create_tables()"
```

### Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Current user info

### Users
- `GET /api/v1/users/` - List users (Manager+)
- `GET /api/v1/users/{user_id}` - Get user details

### TPAs
- `GET /api/v1/tpas/me` - Current TPA info

### Health Plans
- `GET /api/v1/health-plans/` - List health plans
- `POST /api/v1/health-plans/` - Create health plan

### Documents
- `POST /api/v1/documents/upload` - Upload SPD/BPS files
- `GET /api/v1/documents/` - List documents

### Chat
- `POST /api/v1/chat/query` - Submit query
- `GET /api/v1/chat/conversations` - List conversations

### Admin
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/audit-logs` - Audit trail

### Analytics
- `GET /api/v1/analytics/usage` - Usage metrics
- `GET /api/v1/analytics/performance` - Performance stats

## 🔐 Security

### Authentication
- JWT tokens with refresh mechanism
- Role-based access control (RBAC)
- Multi-factor authentication support
- Auth0 integration for enterprise SSO

### Authorization Roles
- **TPA Admin** - Full access to TPA resources
- **CS Manager** - User management, documents, analytics
- **CS Agent** - Query system, basic analytics
- **Member** - Read-only access to own data
- **Readonly** - View-only access

### Data Security
- Multi-tenant data isolation
- HIPAA-compliant audit logging
- Password hashing with bcrypt
- Input validation and sanitization
- Rate limiting and DDoS protection

## 🗄️ Database Schema

### Core Tables
- **tpas** - TPA organizations (root tenant)
- **users** - User accounts with RBAC
- **health_plans** - Insurance plan data
- **documents** - Uploaded files (SPD/BPS)
- **document_chunks** - Vector search content
- **conversations** - Chat sessions
- **messages** - Individual chat messages
- **audit_logs** - Compliance tracking

### Multi-Tenancy
All tenant-specific tables include `tpa_id` foreign key for data isolation.

## 🤖 AI Services

### Vector Search (Pinecone)
- Document chunk embeddings
- Semantic similarity search
- Multi-tenant filtering
- Real-time indexing

### Knowledge Graph (Neo4j)
- Benefit relationships
- Plan hierarchies
- Complex query resolution
- Fallback to in-memory storage

### OpenAI Integration
- Text embeddings (ada-002)
- Response generation (GPT-4)
- Document analysis
- Query intent classification

## 📊 Monitoring

### Logging
- Structured logging with levels
- Request/response logging
- Error tracking with stack traces
- Performance metrics

### Health Checks
- `/health` - Basic health status
- Database connection status
- External service availability
- System resource usage

### Audit Trail
- All user actions logged
- Data access tracking
- Authentication events
- Administrative actions

## 🚀 Deployment

### Docker
```bash
docker build -t smartspd-backend .
docker run -p 8000:8000 smartspd-backend
```

### Docker Compose
```bash
docker-compose up -d
```

### Environment Variables
See `.env.example` for required configuration.

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Load testing
locust -f tests/load_test.py
```

## 📚 Documentation

- API Documentation: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- OpenAPI Schema: http://localhost:8000/api/v1/openapi.json

## 🔍 Troubleshooting

### Common Issues
1. **Database connection failed**
   - Check if PostgreSQL is running
   - Verify DATABASE_URL in .env

2. **Pinecone initialization failed**
   - Verify PINECONE_API_KEY
   - Check index name and environment

3. **Auth0 integration issues**
   - Confirm AUTH0_DOMAIN and credentials
   - Check CORS settings

### Debug Mode
Set `DEBUG=true` in .env for detailed logging and automatic reloading.

## 📞 Support

For technical issues:
- Check logs: `docker-compose logs backend`
- Review API docs for endpoint details
- Validate environment configuration