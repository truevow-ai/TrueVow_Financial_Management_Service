# Development Setup Guide

**Quick Start:** Get the repo running in <20 minutes

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (for PostgreSQL)
- Git

---

## Backend Setup

### Option 1: Automated Script (Recommended)

**Windows (PowerShell):**
```powershell
.\scripts\dev_backend.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/dev_backend.sh
./scripts/dev_backend.sh
```

### Option 2: Manual Setup

```powershell
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env with your DATABASE_URL and JWT_SECRET_KEY

# 4. Start PostgreSQL
docker-compose up -d postgres

# 5. Run migrations
python -m alembic upgrade head

# 6. Run tests
python -m pytest tests/ -v

# 7. Start server
uvicorn app.main:app --reload
```

---

## Frontend Setup

### Option 1: Automated Script (Recommended)

**Windows (PowerShell):**
```powershell
.\scripts\dev_frontend.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/dev_frontend.sh
./scripts/dev_frontend.sh
```

### Option 2: Manual Setup

```powershell
# 1. Navigate to frontend
cd frontend

# 2. Install pnpm (if not installed)
npm install -g pnpm

# 3. Install dependencies
pnpm install

# 4. Run lint
pnpm lint

# 5. Run typecheck
pnpm typecheck

# 6. Build
pnpm build

# 7. Start dev server
pnpm dev
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Generate with: `openssl rand -hex 32`

**Optional:**
- `ENVIRONMENT` - development/production
- `LOG_LEVEL` - INFO/DEBUG
- `BILLING_SERVICE_URL` - For AR sync integration
- `TREASURY_SERVICE_URL` - For treasury integration

---

## Docker Services

Start PostgreSQL:
```powershell
docker-compose up -d postgres
```

Stop PostgreSQL:
```powershell
docker-compose down
```

---

## Verification Commands

After setup, these should all work:

```powershell
# Backend
python -m alembic upgrade head
python -m pytest tests/ -v
uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm lint
pnpm typecheck
pnpm build
```

---

## Troubleshooting

### "Virtual environment not found"
- Run: `python -m venv venv`
- Activate: `.\venv\Scripts\Activate.ps1`

### "ModuleNotFoundError: No module named 'loguru'"
- Activate venv: `.\venv\Scripts\Activate.ps1`
- Install: `pip install -r requirements.txt`

### "DATABASE_URL not set"
- Copy `.env.example` to `.env`
- Fill in `DATABASE_URL` with your PostgreSQL connection string

### "Docker is not running"
- Start Docker Desktop
- Run: `docker-compose up -d postgres`

### "pnpm: command not found"
- Install: `npm install -g pnpm`

---

## Expected Outputs

### Backend Setup Success:
```
✅ Virtual environment created
✅ Dependencies installed
✅ Migrations complete
✅ Tests complete
```

### Frontend Setup Success:
```
✅ Dependencies installed
✅ Lint complete
✅ Typecheck complete
✅ Build complete
```

---

**Setup Time:** <20 minutes for new developers
