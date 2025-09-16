#!/bin/bash

# Seed Test Data Script for Docker Container
# This script can be run manually to reset and seed the database in the Docker environment

echo "🌱 Seeding test data in Docker container..."

# Check if Docker Compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose not found!"
    exit 1
fi

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker containers are not running. Please start them first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "🗑️ Flushing existing database data..."
docker-compose exec web python manage.py flush --noinput

echo "🗄️ Running migrations..."
docker-compose exec web python manage.py migrate --noinput

echo "📊 Creating database views..."
docker-compose exec web python manage.py create_sales_view --force || echo "⚠️ View creation failed"

echo "🌱 Seeding database with test data..."
docker-compose exec web python manage.py seed_data --force

echo "📁 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

echo "✅ Test data seeding completed!"
echo ""
echo "📋 Test accounts created:"
echo "   Admin: username=admin, password=admin123"
echo "   Promoters: username=email, password=promoter123"
echo "   Customers: username=username, password=customer123"
echo ""
echo "🌐 You can now access:"
echo "   Website: http://localhost:8000"
echo "   Admin: http://localhost:8000/admin"
echo "   PgAdmin: http://localhost:5050"
