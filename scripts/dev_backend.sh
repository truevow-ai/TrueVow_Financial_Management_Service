#!/bin/bash
# Development setup script for backend
# Usage: ./scripts/dev_backend.sh

set -e

echo "=========================================="
echo "TrueVow FM Service - Backend Dev Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your actual values."
        echo "   Required: DATABASE_URL, JWT_SECRET_KEY"
        exit 1
    else
        echo "❌ .env.example not found. Cannot proceed."
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running. Starting PostgreSQL container..."
    echo "   Please start Docker Desktop and run: docker-compose up -d postgres"
    exit 1
fi

# Start PostgreSQL if not running
if ! docker ps | grep -q fm-postgres; then
    echo "🐘 Starting PostgreSQL container..."
    docker-compose up -d postgres
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Run migrations
echo "🔄 Running database migrations..."
python -m alembic upgrade head
echo "✅ Migrations complete"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v
echo "✅ Tests complete"

echo ""
echo "=========================================="
echo "✅ Backend setup complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
