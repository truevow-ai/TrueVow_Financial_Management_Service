# Development setup script for frontend (PowerShell)
# Usage: .\scripts\dev_frontend.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TrueVow FM Service - Frontend Dev Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node -v
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check Node.js version
$nodeMajorVersion = (node -v).Substring(1).Split('.')[0]
if ([int]$nodeMajorVersion -lt 18) {
    Write-Host "❌ Node.js version 18+ required. Current version: $(node -v)" -ForegroundColor Red
    exit 1
}

# Check if pnpm is installed
try {
    pnpm -v | Out-Null
    Write-Host "✅ pnpm found" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing pnpm..." -ForegroundColor Cyan
    npm install -g pnpm
    Write-Host "✅ pnpm installed" -ForegroundColor Green
}

# Navigate to frontend directory
Set-Location frontend

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
pnpm install
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Run lint
Write-Host "🔍 Running linter..." -ForegroundColor Cyan
pnpm lint
Write-Host "✅ Lint complete" -ForegroundColor Green

# Run typecheck
Write-Host "🔍 Running typecheck..." -ForegroundColor Cyan
pnpm typecheck
Write-Host "✅ Typecheck complete" -ForegroundColor Green

# Build
Write-Host "🏗️  Building..." -ForegroundColor Cyan
pnpm build
Write-Host "✅ Build complete" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Frontend setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the dev server:" -ForegroundColor Yellow
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  pnpm dev" -ForegroundColor White
Write-Host ""

Set-Location ..
