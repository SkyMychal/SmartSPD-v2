#!/bin/bash

# SmartSPD v2 Development Startup Script
echo "🚀 Starting SmartSPD v2 Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start infrastructure services
echo "📦 Starting infrastructure services (PostgreSQL, Redis, Neo4j)..."
docker-compose up -d postgres redis neo4j

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."
docker-compose ps

# Run database migrations
echo "📊 Running database migrations..."
cd backend
python -c "
import sys
sys.path.append('.')
from app.core.database import create_tables
create_tables()
print('✅ Database tables created successfully')
"

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python -m venv venv
fi

echo "📦 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Start FastAPI backend
echo "🔧 Starting FastAPI backend..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ../frontend
if [ -f "package.json" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    
    echo "⚛️ Starting Next.js frontend..."
    npm run dev &
    FRONTEND_PID=$!
fi

echo ""
echo "🎉 SmartSPD v2 is starting up!"
echo ""
echo "📍 Services:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/api/v1/docs"
echo "   • Frontend: http://localhost:3000 (when available)"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo "   • Neo4j Browser: http://localhost:7474"
echo ""
echo "📚 Credentials:"
echo "   • PostgreSQL: smartspd_user / smartspd_password"
echo "   • Neo4j: neo4j / smartspd_password"
echo ""
echo "🛠️ Development Commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart: ./start_development.sh"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; docker-compose down; exit 0' INT

# Keep script running
wait