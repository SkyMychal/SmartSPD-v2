#!/bin/bash

# Better development startup script
# Handles different environments automatically

echo "🚀 Starting SmartSPD v2 Development Environment"
echo "Environment detection:"

# Detect environment
if [ -n "$CODESPACE_NAME" ]; then
    echo "📱 GitHub Codespace detected: $CODESPACE_NAME"
    ENVIRONMENT="codespace"
elif [ -n "$DOCKER_HOST" ] || command -v docker-compose &> /dev/null; then
    echo "🐳 Docker environment detected"
    ENVIRONMENT="docker"
else
    echo "💻 Local development environment"
    ENVIRONMENT="local"
fi

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    echo "⏳ Waiting for $service_name..."
    
    for i in {1..30}; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $i/30: $service_name not ready yet..."
        sleep 2
    done
    
    echo "❌ $service_name failed to start after 60 seconds"
    return 1
}

# Start services based on environment
case $ENVIRONMENT in
    "codespace")
        echo "🚀 Starting all services with Docker Compose..."
        docker-compose up -d
        
        # Wait for backend
        wait_for_service "https://$CODESPACE_NAME-8000.app.github.dev/health" "Backend API"
        
        # Frontend should auto-start via Docker Compose
        wait_for_service "https://$CODESPACE_NAME-3000.app.github.dev" "Frontend"
        
        echo "🎉 All services ready!"
        echo "Frontend: https://$CODESPACE_NAME-3000.app.github.dev"
        echo "Backend: https://$CODESPACE_NAME-8000.app.github.dev"
        ;;
        
    "docker")
        echo "🚀 Starting all services with Docker Compose..."
        docker-compose up -d
        
        wait_for_service "http://localhost:8000/health" "Backend API"
        wait_for_service "http://localhost:3000" "Frontend"
        
        echo "🎉 All services ready!"
        echo "Frontend: http://localhost:3000"
        echo "Backend: http://localhost:8000"
        ;;
        
    "local")
        echo "🚀 Starting services locally..."
        
        # Start database services
        docker-compose up -d postgres redis
        wait_for_service "http://localhost:5432" "PostgreSQL" || echo "⚠️ PostgreSQL might need more time"
        wait_for_service "http://localhost:6379" "Redis" || echo "⚠️ Redis might need more time"
        
        # Start backend locally
        echo "Starting backend..."
        cd backend
        if [ ! -d "venv" ]; then
            python -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
        fi
        source venv/bin/activate
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd ..
        
        # Start frontend locally
        echo "Starting frontend..."
        cd frontend
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        
        wait_for_service "http://localhost:8000/health" "Backend API"
        wait_for_service "http://localhost:3000" "Frontend"
        
        echo "🎉 All services ready!"
        echo "Frontend: http://localhost:3000"
        echo "Backend: http://localhost:8000"
        echo ""
        echo "To stop services: kill $BACKEND_PID $FRONTEND_PID"
        ;;
esac

echo ""
echo "📝 Login credentials:"
echo "Admin: sstillwagon@kemptongroup.com / temp123"
echo ""
echo "🔧 To check logs:"
echo "docker-compose logs -f [service-name]"