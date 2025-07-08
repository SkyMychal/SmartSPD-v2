#!/bin/bash
set -e

# SmartSPD Backend Production Entrypoint Script

echo "Starting SmartSPD Backend..."

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-smartspd_user}" -d "${POSTGRES_DB:-smartspd}"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

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

# Set proper permissions
chown -R appuser:appuser /app/uploads /app/logs

echo "Starting application with command: $@"
exec "$@"