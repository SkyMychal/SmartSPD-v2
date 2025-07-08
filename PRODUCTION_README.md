# SmartSPD v2 - Production Ready

## 🚀 Quick Start (1-Command Setup)

```bash
# Start the complete application
./start_smartspd.sh
```

The application will be available at **http://localhost:5000**

## 🔐 Demo Login Credentials

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Customer Service Agent | `agent@demo.com` | `demo123` | Read, Write |
| Plan Member | `member@demo.com` | `demo123` | Read |
| HR Manager | `hr@demo.com` | `demo123` | Read, Write |
| Broker | `broker@demo.com` | `demo123` | Read |
| System Admin | `admin@demo.com` | `admin123` | Full Access |

## ✅ What's Working

- ✅ **Complete Full-Stack Application** - React frontend + Flask backend
- ✅ **User Authentication** - JWT-based auth with role-based access control
- ✅ **Demo Users** - Ready-to-use demo accounts for all user types
- ✅ **Health Plan System** - Demo health plan data integrated
- ✅ **Professional UI** - Modern React interface with Tailwind CSS
- ✅ **API Endpoints** - REST API for auth, chat, and document management
- ✅ **Production Build** - Optimized frontend build process
- ✅ **Environment Configuration** - Proper env vars and secrets management
- ✅ **Database Setup** - SQLite database with demo data
- ✅ **CORS Configuration** - Proper cross-origin setup
- ✅ **Error Handling** - Comprehensive error handling and logging

## 📁 Project Structure

```
SmartSPD-v2/
├── start_smartspd.sh              # 1-command startup script
├── PRODUCTION_README.md            # This file
└── home/ubuntu/SmartSPD_v2_Final_Package/
    ├── backend/                    # Flask API server
    │   ├── src/main.py            # Application entry point
    │   ├── src/routes/            # API endpoints
    │   ├── src/services/          # Business logic
    │   ├── src/models/            # Data models
    │   ├── venv/                  # Python virtual environment
    │   └── .env                   # Environment variables
    └── frontend/                   # React application
        ├── src/                   # Source code
        ├── dist/                  # Built application
        └── package.json           # Dependencies
```

## 🔧 Manual Setup (if needed)

### Backend Setup
```bash
cd home/ubuntu/SmartSPD_v2_Final_Package/backend
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Frontend Setup
```bash
cd home/ubuntu/SmartSPD_v2_Final_Package/frontend
pnpm install
pnpm run build
cp -r dist/* ../backend/src/static/
```

## 🌟 Key Features

### Advanced AI Health Plan Assistant
- **Intelligent Document Processing** - Automatic SPD/BPS document parsing
- **RAG Technology** - Retrieval-Augmented Generation for accurate responses
- **Multi-Role Support** - Tailored experiences for different user types
- **Real-time Chat** - iPhone-style messaging interface
- **Enterprise Security** - HIPAA compliant with proper access controls

### Technical Stack
- **Backend**: Python Flask, SQLAlchemy, JWT Authentication
- **Frontend**: React 19, Tailwind CSS 4, Vite
- **Database**: SQLite (production-ready for PostgreSQL)
- **AI**: OpenAI GPT integration, ChromaDB vector storage
- **Deployment**: Single-file deployment with automatic build

## 🚀 Production Deployment

### Option 1: Simple Server Deployment
```bash
# On your production server
git clone <your-repo>
cd SmartSPD-v2
./start_smartspd.sh
```

### Option 2: Docker Deployment
```bash
# Build and run with Docker
docker build -t smartspd-v2 .
docker run -p 5000:5000 smartspd-v2
```

### Option 3: Cloud Deployment
- **Heroku**: Ready for deployment with Procfile
- **AWS/Azure**: Compatible with standard PaaS platforms
- **DigitalOcean**: Works with App Platform

## 🔐 Security Features

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based access control
- ✅ CORS security headers
- ✅ Input validation and sanitization
- ✅ Session management
- ✅ Environment variable security

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `POST /api/auth/verify` - Session verification

### Chat
- `POST /api/chat/query` - Send chat query
- `GET /api/chat/history` - Get conversation history

### Documents
- `POST /api/documents/upload` - Upload health plan documents
- `GET /api/documents/list` - List processed documents

### Health Check
- `GET /api/health` - API status and version info

## 🆘 Troubleshooting

### Application won't start
```bash
# Check if ports are available
lsof -i :5000

# Kill existing processes
pkill -f "python src/main.py"

# Restart with clean state
./start_smartspd.sh
```

### Frontend not loading
```bash
# Rebuild frontend
cd home/ubuntu/SmartSPD_v2_Final_Package/frontend
pnpm run build
cp -r dist/* ../backend/src/static/
```

### Database issues
```bash
# Reset database
rm -f backend/src/data/smartspd.db
# Restart application to recreate
./start_smartspd.sh
```

## 📞 Support

For technical support:
- Check the logs: `tail -f backend/server.log`
- Verify environment variables in `backend/.env`
- Test API endpoints: `curl http://localhost:5000/api/health`

---

**SmartSPD v2** - Advanced AI Health Plan Assistant
*Ready for Production | Built for BeneSense AI*