#!/bin/bash
set -e

# SmartSPD v2 Backup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_ROOT="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
RETENTION_DAYS=30

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

create_backup_directory() {
    log_info "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

backup_database() {
    log_info "Backing up PostgreSQL database..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_warning "PostgreSQL container is not running"
        return 1
    fi
    
    # Create database backup
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U smartspd_user \
        -d smartspd \
        --verbose \
        --format=custom \
        --compress=9 \
        --blobs > "$BACKUP_DIR/database.backup"
    
    # Create SQL dump as well
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U smartspd_user \
        -d smartspd \
        --verbose > "$BACKUP_DIR/database.sql"
    
    log_success "Database backup completed"
}

backup_redis() {
    log_info "Backing up Redis data..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        log_warning "Redis container is not running"
        return 1
    fi
    
    # Create Redis backup
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli BGSAVE
    sleep 5  # Wait for background save to complete
    
    # Copy dump file
    docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis-dump.rdb"
    
    log_success "Redis backup completed"
}

backup_neo4j() {
    log_info "Backing up Neo4j data..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps neo4j | grep -q "Up"; then
        log_warning "Neo4j container is not running"
        return 1
    fi
    
    # Create Neo4j backup directory
    mkdir -p "$BACKUP_DIR/neo4j"
    
    # Export Neo4j data
    docker-compose -f "$COMPOSE_FILE" exec -T neo4j cypher-shell \
        -u neo4j -p "$NEO4J_PASSWORD" \
        "CALL apoc.export.cypher.all('backup.cypher', {format: 'cypher-shell', useOptimizations: {type: 'UNWIND_BATCH', unwindBatchSize: 20}})" \
        > "$BACKUP_DIR/neo4j/export.log" 2>&1 || true
    
    # Copy the backup file
    docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q neo4j):/var/lib/neo4j/import/backup.cypher "$BACKUP_DIR/neo4j/" 2>/dev/null || true
    
    log_success "Neo4j backup completed"
}

backup_uploads() {
    log_info "Backing up uploaded files..."
    
    # Check if uploads volume exists
    if docker volume ls | grep -q "smartspd-v2_uploads_data"; then
        # Create temporary container to access volume
        docker run --rm -v smartspd-v2_uploads_data:/uploads -v "$PWD/$BACKUP_DIR":/backup ubuntu tar czf /backup/uploads.tar.gz -C /uploads .
        log_success "Uploads backup completed"
    else
        log_warning "No uploads volume found"
    fi
}

backup_logs() {
    log_info "Backing up application logs..."
    
    # Check if logs volume exists
    if docker volume ls | grep -q "smartspd-v2_logs_data"; then
        # Create temporary container to access volume
        docker run --rm -v smartspd-v2_logs_data:/logs -v "$PWD/$BACKUP_DIR":/backup ubuntu tar czf /backup/logs.tar.gz -C /logs .
        log_success "Logs backup completed"
    else
        log_warning "No logs volume found"
    fi
}

backup_configuration() {
    log_info "Backing up configuration files..."
    
    # Copy configuration files
    cp -r docker "$BACKUP_DIR/"
    cp "$COMPOSE_FILE" "$BACKUP_DIR/"
    cp .env.prod "$BACKUP_DIR/" 2>/dev/null || true
    
    log_success "Configuration backup completed"
}

create_backup_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/manifest.txt" << EOF
SmartSPD v2 Backup Manifest
Created: $(date)
Backup ID: $TIMESTAMP

Contents:
- PostgreSQL database (database.backup, database.sql)
- Redis data (redis-dump.rdb)
- Neo4j data (neo4j/)
- Uploaded files (uploads.tar.gz)
- Application logs (logs.tar.gz)
- Configuration files (docker/, docker-compose.prod.yml, .env.prod)

System Information:
$(docker version --format "Docker {{.Server.Version}}")
$(docker-compose version --short)

Services Status:
$(docker-compose -f "$COMPOSE_FILE" ps)
EOF
    
    log_success "Backup manifest created"
}

compress_backup() {
    log_info "Compressing backup..."
    
    cd "$BACKUP_ROOT"
    tar czf "$TIMESTAMP.tar.gz" "$TIMESTAMP"
    rm -rf "$TIMESTAMP"
    
    log_success "Backup compressed: $BACKUP_ROOT/$TIMESTAMP.tar.gz"
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_ROOT" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    log_success "Old backups cleaned up"
}

verify_backup() {
    log_info "Verifying backup integrity..."
    
    if [ -f "$BACKUP_ROOT/$TIMESTAMP.tar.gz" ]; then
        if tar tzf "$BACKUP_ROOT/$TIMESTAMP.tar.gz" > /dev/null; then
            log_success "Backup verification passed"
            return 0
        else
            log_error "Backup verification failed"
            return 1
        fi
    else
        log_error "Backup file not found"
        return 1
    fi
}

show_backup_info() {
    local backup_file="$BACKUP_ROOT/$TIMESTAMP.tar.gz"
    local size=$(du -h "$backup_file" | cut -f1)
    
    log_success "Backup completed successfully!"
    echo ""
    log_info "Backup Details:"
    echo "  File: $backup_file"
    echo "  Size: $size"
    echo "  Timestamp: $TIMESTAMP"
    echo ""
    log_info "To restore this backup, use:"
    echo "  ./scripts/restore.sh $TIMESTAMP"
}

# Main backup process
main() {
    log_info "Starting SmartSPD v2 backup..."
    
    # Load environment variables
    if [ -f ".env.prod" ]; then
        source .env.prod
    fi
    
    create_backup_directory
    
    # Perform backups
    backup_database
    backup_redis
    backup_neo4j
    backup_uploads
    backup_logs
    backup_configuration
    create_backup_manifest
    
    # Compress and verify
    compress_backup
    
    if verify_backup; then
        cleanup_old_backups
        show_backup_info
    else
        log_error "Backup verification failed"
        exit 1
    fi
}

# Handle script arguments
case "$1" in
    "database")
        create_backup_directory
        backup_database
        ;;
    "files")
        create_backup_directory
        backup_uploads
        ;;
    "config")
        create_backup_directory
        backup_configuration
        ;;
    "verify")
        if [ -n "$2" ]; then
            verify_backup "$2"
        else
            log_error "Please specify backup timestamp to verify"
            exit 1
        fi
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    *)
        main
        ;;
esac