#!/bin/bash
set -e

# SmartSPD v2 Production Deployment Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        log_info "Copy .env.production to $ENV_FILE and configure your settings"
        exit 1
    fi
    
    log_success "All requirements met"
}

create_backup() {
    log_info "Creating backup before deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database if running
    if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_info "Backing up PostgreSQL database..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U smartspd_user smartspd > "$BACKUP_DIR/database.sql"
        log_success "Database backup created: $BACKUP_DIR/database.sql"
    fi
    
    # Backup uploaded files
    if [ -d "./uploads" ]; then
        log_info "Backing up uploaded files..."
        cp -r ./uploads "$BACKUP_DIR/uploads"
        log_success "Files backup created: $BACKUP_DIR/uploads"
    fi
    
    log_success "Backup completed: $BACKUP_DIR"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker-compose -f "$COMPOSE_FILE" build backend
    
    # Build frontend image
    log_info "Building frontend image..."
    docker-compose -f "$COMPOSE_FILE" build frontend
    
    log_success "Images built successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start database services first
    log_info "Starting database services..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis neo4j
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    sleep 30
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d backend frontend nginx
    
    log_success "Services deployed successfully"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check backend health
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Check frontend health
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    # Check nginx
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Nginx health check passed"
    else
        log_error "Nginx health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

show_status() {
    log_info "Deployment status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log_info "Application URLs:"
    echo "  Frontend: http://localhost"
    echo "  Backend API: http://localhost/api/v1"
    echo "  Neo4j Browser: http://localhost:7474"
    echo ""
    log_info "Logs can be viewed with:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f [service_name]"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    log_success "Cleanup completed"
}

# Main deployment process
main() {
    log_info "Starting SmartSPD v2 production deployment..."
    
    check_requirements
    
    if [ "$1" != "--no-backup" ]; then
        create_backup
    fi
    
    build_images
    deploy_services
    
    if run_health_checks; then
        show_status
        cleanup_old_images
        log_success "Deployment completed successfully!"
    else
        log_error "Deployment failed health checks"
        log_info "Check logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi
}

# Handle script arguments
case "$1" in
    "backup")
        create_backup
        ;;
    "build")
        build_images
        ;;
    "deploy")
        deploy_services
        ;;
    "health")
        run_health_checks
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup_old_images
        ;;
    *)
        main "$@"
        ;;
esac