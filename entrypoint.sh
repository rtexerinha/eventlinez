#!/bin/bash

# Docker Entrypoint Script for Eventlinez
# This script ensures proper initialization in Docker environment

set -e

echo "🚀 Starting Eventlinez Docker container..."

# Setup Google Cloud authentication if service account key is provided
if [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS_BASE64" ]; then
    echo "🔐 Setting up Google Cloud authentication from base64..."
    echo "$GOOGLE_APPLICATION_CREDENTIALS_BASE64" | base64 -d > /app/service-account-key.json
    chmod 600 /app/service-account-key.json
    export GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
    echo "✅ Google Cloud authentication configured"
elif [ -f "/app/service-account-key.json" ] && [ -s "/app/service-account-key.json" ]; then
    echo "🔐 Using existing Google Cloud service account key..."
    export GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
else
    echo "⚠️ No Google Cloud service account key found - reCAPTCHA Enterprise will fall back to standard API"
fi

# Function to wait for the database to be ready
postgres_ready() {
    python << END
import sys
import psycopg2
import os

try:
    dbname = os.getenv("POSTGRES_DB", "eventlinez")
    user = os.getenv("POSTGRES_USER", "eventlinez")
    password = os.getenv("POSTGRES_PASSWORD", "Texera123@")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")

    print(f"🔌 Attempting to connect to PostgreSQL at {host}:{port}")
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    conn.close()
    print("✅ PostgreSQL connection successful")
except psycopg2.OperationalError as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    sys.exit(-1)
sys.exit(0)
END
}

# Wait for the database to be ready
echo "🔍 Waiting for PostgreSQL to be ready..."
until postgres_ready; do
  echo "⏳ PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "🗄️ PostgreSQL is up - running migrations..."

# Drop problematic views before migrations (consistent with deployment script)
echo "🔧 Dropping problematic database views..."
python manage.py drop_views --force || echo "⚠️ Could not drop views (might not exist)"

# Run database migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Create database views safely after migrations
echo "🏗️ Creating database views..."
python manage.py create_sales_view --force || echo "⚠️ Could not create sales view (might not be needed)"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Check if we should seed data for test environment
if [ "$ENVIRONMENT" = "test" ] || [ "$SEED_DATA" = "true" ]; then
    echo "🌱 Seeding database with test data (test environment)..."
    python manage.py seed_data --force || echo "⚠️ Database seeding failed"
fi

echo "✅ Initialization complete!"

# Execute the passed command
echo "🚀 Starting application: $@"
exec "$@"
