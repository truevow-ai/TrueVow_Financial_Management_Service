#!/bin/bash
# Development setup script for frontend
# Usage: ./scripts/dev_frontend.sh

set -e

echo "=========================================="
echo "TrueVow FM Service - Frontend Dev Setup"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ required. Current version: $(node -v)"
    exit 1
fi

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
    echo "✅ pnpm installed"
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📥 Installing dependencies..."
pnpm install
echo "✅ Dependencies installed"

# Run lint
echo "🔍 Running linter..."
pnpm lint
echo "✅ Lint complete"

# Run typecheck
echo "🔍 Running typecheck..."
pnpm typecheck
echo "✅ Typecheck complete"

# Build
echo "🏗️  Building..."
pnpm build
echo "✅ Build complete"

echo ""
echo "=========================================="
echo "✅ Frontend setup complete!"
echo "=========================================="
echo ""
echo "To start the dev server:"
echo "  cd frontend"
echo "  pnpm dev"
echo ""
