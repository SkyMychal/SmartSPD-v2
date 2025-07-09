#!/bin/bash
set -e

# SmartSPD Backend Production Entrypoint Script

echo "Starting SmartSPD Backend..."

# Simple wait for services (they should be healthy already)
echo "Waiting for services to be ready..."
sleep 5
echo "Services should be ready, starting application..."

# Run database migrations
echo "Running database migrations..."
if [ -f "/app/alembic/alembic.ini" ]; then
    cd /app && alembic upgrade head
else
    echo "No Alembic configuration found, skipping migrations"
fi

# Create upload directories if they don't exist
mkdir -p /app/uploads
mkdir -p /app/logs

# Set proper permissions (ignore errors for existing files)
chown -R appuser:appuser /app/uploads /app/logs 2>/dev/null || true

echo "Starting application with command: $@"
exec "$@"