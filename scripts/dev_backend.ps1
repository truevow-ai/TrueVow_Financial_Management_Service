# Development setup script for backend (PowerShell)
# Usage: .\scripts\dev_backend.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TrueVow FM Service - Backend Dev Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Require .env or .env.local (FINANCIAL_MANAGEMENT_* vars typically live in .env.local)
$hasEnv = (Test-Path .env) -or (Test-Path .env.local)
if (-not $hasEnv) {
    Write-Host "[!] No .env or .env.local found. Creating .env from .env.example..." -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "[ok] Created .env. Edit with DATABASE_URL or FINANCIAL_MANAGEMENT_DATABASE_URL, JWT_SECRET_KEY or FINANCIAL_MANAGEMENT_SECRET_KEY." -ForegroundColor Green
        exit 1
    } else {
        Write-Host "[X] .env.example not found. Create .env or .env.local with required keys." -ForegroundColor Red
        exit 1
    }
}

# Load .env and .env.local into process env so Alembic/pytest see FINANCIAL_MANAGEMENT_* and JWT_*
function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path -Raw | ForEach-Object {
        $_ -split "`n" | ForEach-Object {
            $line = $_.Trim()
            if ($line -eq "" -or $line.StartsWith("#")) { return }
            if ($line -match '^([^#=]+)=(.*)$') {
                $k = $matches[1].Trim(); $v = $matches[2].Trim()
                if ($v.StartsWith('"') -and $v.EndsWith('"')) { $v = $v.Substring(1, $v.Length - 2) }
                if ($v.StartsWith("'") -and $v.EndsWith("'")) { $v = $v.Substring(1, $v.Length - 2) }
                Set-Item -Path "Env:$k" -Value $v -Force
            }
        }
    }
}
Load-DotEnv ".env"
Load-DotEnv ".env.local"
Write-Host "Loaded env from .env and .env.local (FINANCIAL_MANAGEMENT_* and JWT_* available)" -ForegroundColor Gray

# Check if virtual environment exists
if (-not (Test-Path venv)) {
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "[ok] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[*] Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "[*] Installing dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
# On Python 3.13, avoid cached pydantic-core source builds (need Rust); use fresh wheels
$pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
$useNoCache = ($pyVer -and $pyVer.StartsWith("3.13"))
if ($useNoCache) {
    Write-Host "[*] Python 3.13 detected: installing without cache to use prebuilt wheels" -ForegroundColor Gray
    pip install -r requirements.txt --no-cache-dir
} else {
    pip install -r requirements.txt
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] pip install failed. Fix errors above and re-run." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[ok] Dependencies installed" -ForegroundColor Green

# Docker/Postgres only when using local DB; skip when FINANCIAL_MANAGEMENT_DATABASE_URL is set (e.g. Supabase)
$dbUrl = $env:FINANCIAL_MANAGEMENT_DATABASE_URL; if (-not $dbUrl) { $dbUrl = $env:DATABASE_URL }
$useLocalPostgres = (-not $dbUrl) -or ($dbUrl -match "localhost|127\.0\.0\.1")
if ($useLocalPostgres) {
    try {
        docker info | Out-Null
        $dockerRunning = $true
    } catch {
        $dockerRunning = $false
    }
    if (-not $dockerRunning) {
        Write-Host "[!] Docker is not running. Start Docker, or set FINANCIAL_MANAGEMENT_DATABASE_URL to a remote DB (e.g. Supabase)." -ForegroundColor Yellow
        exit 1
    }
    $postgresRunning = docker ps | Select-String "fm-postgres"
    if (-not $postgresRunning) {
        Write-Host "[*] Starting PostgreSQL container..." -ForegroundColor Cyan
        docker-compose up -d postgres
        Write-Host "[*] Waiting for PostgreSQL to be ready..." -ForegroundColor Cyan
        Start-Sleep -Seconds 5
    }
} else {
    Write-Host "[*] Using remote DB URL (Docker check skipped)" -ForegroundColor Gray
}

# Run migrations
Write-Host "[*] Running database migrations..." -ForegroundColor Cyan
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Migrations failed. Fix errors above and re-run." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[ok] Migrations complete" -ForegroundColor Green

# Run tests
Write-Host "[*] Running tests..." -ForegroundColor Cyan
python -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Tests failed or no pytest. Fix errors above." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[ok] Tests complete" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backend setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the server:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python -m uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
