#!/bin/bash

# Docker Deployment Script for Eventlinez with reCAPTCHA Enterprise
# This script helps you build and deploy the application with proper reCAPTCHA configuration

set -e

echo "🐳 Eventlinez Docker Deployment with reCAPTCHA Enterprise"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are available"

# Check if .env.docker exists
if [ ! -f ".env.docker" ]; then
    print_warning ".env.docker file not found. Creating from template..."
    cp .env.example .env.docker
    print_warning "Please edit .env.docker with your actual reCAPTCHA keys before proceeding"
    exit 1
fi

# Check for reCAPTCHA configuration
if grep -q "your-private-key-here" .env.docker; then
    print_warning "Please configure your actual reCAPTCHA keys in .env.docker before deploying"
    echo "Required variables:"
    echo "  - RECAPTCHA_PUBLIC_KEY"
    echo "  - RECAPTCHA_PRIVATE_KEY" 
    echo "  - RECAPTCHA_PROJECT_ID (for Enterprise API)"
    exit 1
fi

# Parse command line arguments
BUILD_FRESH=false
SEED_DATA=false
PRODUCTION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            BUILD_FRESH=true
            shift
            ;;
        --seed|-s)
            SEED_DATA=true
            shift
            ;;
        --production|-p)
            PRODUCTION=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --build, -b     Force rebuild of Docker images"
            echo "  --seed, -s      Seed database with test data"
            echo "  --production, -p  Deploy in production mode"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Build images if requested or if they don't exist
if [ "$BUILD_FRESH" = true ] || ! docker images | grep -q eventlinez; then
    print_status "Building Docker images..."
    docker-compose build --no-cache
else
    print_status "Using existing Docker images (use --build to rebuild)"
fi

# Set environment variables for deployment
export SEED_DATA=$SEED_DATA
if [ "$PRODUCTION" = true ]; then
    export DEBUG=False
    export PROD=True
    print_status "Deploying in production mode"
else
    export DEBUG=True
    export PROD=False
    print_status "Deploying in development mode"
fi

# Start services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_status "Services are running successfully!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   - Main app: http://localhost:8000"
    echo "   - Contact page: http://localhost:8000/contact/"
    echo "   - PgAdmin: http://localhost:5050"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "📝 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    
    # Test reCAPTCHA configuration
    echo ""
    print_status "Testing reCAPTCHA configuration..."
    if docker-compose exec -T web python -c "
import os
from shop.recaptcha_utils import RECAPTCHA_ENTERPRISE_AVAILABLE, REQUESTS_AVAILABLE
print(f'reCAPTCHA Enterprise available: {RECAPTCHA_ENTERPRISE_AVAILABLE}')
print(f'Requests library available: {REQUESTS_AVAILABLE}')
print(f'Public key configured: {bool(os.getenv(\"RECAPTCHA_PUBLIC_KEY\"))}')
print(f'Private key configured: {bool(os.getenv(\"RECAPTCHA_PRIVATE_KEY\"))}')
print(f'Project ID configured: {bool(os.getenv(\"RECAPTCHA_PROJECT_ID\"))}')
" 2>/dev/null; then
        print_status "reCAPTCHA configuration test completed"
    else
        print_warning "Could not test reCAPTCHA configuration - check logs if issues occur"
    fi
    
else
    print_error "Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi