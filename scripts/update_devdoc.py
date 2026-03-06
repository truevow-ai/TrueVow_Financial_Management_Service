#!/usr/bin/env python
"""Update Developer Documentation for TrueVow Financial Management Service."""

import os
import sys
from datetime import datetime

# External documentation path (universal for all repos)
DOC_PATH = r"C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation"

# Target developer documentation file
DEV_DOC_FILE = os.path.join(DOC_PATH, "TrueVow-Financial-Management-Dev-Guide.md")

def main():
    """Update the developer documentation with recent architectural changes."""
    
    # Check if documentation directory exists
    if not os.path.exists(DOC_PATH):
        print(f"❌ Documentation directory not found: {DOC_PATH}")
        sys.exit(1)
    
    # Create developer documentation file if it doesn't exist
    if not os.path.exists(DEV_DOC_FILE):
        print(f"📝 Creating new developer documentation file: {DEV_DOC_FILE}")
        initial_content = f"""# TrueVow Financial Management Service - Developer Guide

> **Version:** 1.0
> **Last Updated:** {datetime.now().strftime('%B %Y')}
> **Status:** ✅ DEVELOPMENT ENVIRONMENT READY | 🔄 ACTIVE CONTRIBUTION WELCOME

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- pnpm (recommended) or npm

### Initial Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd TrueVow-Financial-Management

# 2. Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate  # Windows

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend
pnpm install
cd ..

# 5. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 6. Run database migrations
alembic upgrade head

# 7. Seed the database
python scripts/seed_database.py

# 8. Start development servers
# Terminal 1: Backend
uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd frontend
pnpm dev
```

## 🏗️ Project Structure

```
TrueVow-Financial-Management/
├── app/                    # Backend FastAPI application
│   ├── api/               # API routes
│   │   └── v1/           # Version 1 API
│   ├── auth/             # Authentication middleware
│   ├── core/             # Core utilities and config
│   ├── modules/          # Business modules
│   │   ├── general_ledger/
│   │   ├── accounts_receivable/
│   │   ├── accounts_payable/
│   │   └── ...
│   └── main.py           # FastAPI app entry point
├── frontend/             # Next.js frontend
│   ├── app/              # App router pages
│   ├── components/       # React components
│   ├── contexts/         # React contexts
│   ├── hooks/            # Custom hooks
│   └── lib/              # Utility libraries
├── infra/database/        # Database files
│   ├── migrations/       # Alembic migrations
│   └── seed/            # Seed data
├── scripts/              # Utility scripts
└── tests/                # Test files
```

## 🔧 Development Workflow

### Backend Development

#### Creating New API Endpoints
1. Create model in `app/modules/<module>/models/`
2. Create service in `app/modules/<module>/services/`
3. Create routes in `app/modules/<module>/api/routes/`
4. Register routes in `app/api/v1/__init__.py`
5. Add tests in `tests/`

#### Example: Adding a New Endpoint
```python
# app/modules/general_ledger/api/routes/example_routes.py
from fastapi import APIRouter, Depends
from app.core.database import get_db_session

router = APIRouter(prefix="/example", tags=["Example"])

@router.get("/")
async def get_examples(db: AsyncSession = Depends(get_db_session)):
    # Implementation here
    pass
```

### Frontend Development

#### Creating New Components
1. Create component in `frontend/components/`
2. Add types in `frontend/types/`
3. Create hooks if needed in `frontend/hooks/`
4. Add to pages in `frontend/app/`

#### Example: Creating a New Page
```typescript
// frontend/app/example/page.tsx
'use client'

import {{ useQuery }} from '@tanstack/react-query'
import {{ exampleApi }} from '@/lib/api/exampleApi'

export default function ExamplePage() {{
  const {{ data, isLoading }} = useQuery({{
    queryKey: ['examples'],
    queryFn: () => exampleApi.getExamples()
  }})

  if (isLoading) return <div>Loading...</div>
  
  return (
    <div>
      {{data?.map(item => (
        <div key={{item.id}}>{{item.name}}</div>
      ))}}
    </div>
  )
}}
```

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_example.py

# Run with coverage
python -m pytest --cov=app tests/

# Run integration tests
python -m pytest tests/integration/
```

### Frontend Testing
```bash
cd frontend

# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run with coverage
pnpm test:coverage

# Run E2E tests
pnpm test:e2e
```

## 🔍 Debugging

### Backend Debugging
```bash
# Run with debug logging
uvicorn app.main:app --reload --log-level debug

# Debug database queries
echo "SET application_name='debug'; SELECT * FROM legal_entity;" | psql $DATABASE_URL
```

### Frontend Debugging
```bash
# Enable React DevTools
# In browser console:
window.__REACT_DEVTOOLS_GLOBAL_HOOK__.inject = function(){{}}

# Debug React Query
# In browser console:
window.reactQueryDevtools.open()
```

## 📦 Code Quality

### Running Linters
```bash
# Backend
ruff check .
mypy .

# Frontend
cd frontend
pnpm lint
pnpm typecheck
```

### Formatting Code
```bash
# Backend
black .
ruff format .

# Frontend
cd frontend
pnpm format
```

## 🔐 Authentication Development

### Testing Authenticated Requests
```python
# Backend test with auth
import pytest
from app.auth.middleware import create_test_token

def test_protected_endpoint(client):
    token = create_test_token(user_id="test-user", roles=["admin"])
    response = client.get("/api/v1/entities", headers={{"Authorization": f"Bearer {{token}}"}})
    assert response.status_code == 200
```

### Frontend Auth Testing
```typescript
// Mock Clerk auth in tests
import {{ mockClerk }} from '@/__tests__/mocks/clerk'

describe('Protected Component', () => {{
  beforeEach(() => {{
    mockClerk()
  }})
  
  // Test implementation
}})
```

## 🚨 Common Issues & Solutions

### Database Connection Issues
```bash
# Check database connectivity
python -c "import psycopg2; print('Connected successfully')"

# Reset database
dropdb fm_database
createdb fm_database
alembic upgrade head
python scripts/seed_database.py
```

### Frontend Build Issues
```bash
# Clear Next.js cache
cd frontend
rm -rf .next
pnpm dev

# Clear node_modules
rm -rf node_modules
pnpm install
```

### Authentication Issues
```bash
# Check Clerk configuration
echo $NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

# Test token validation
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/auth/me
```

## 📚 Learning Resources

### Official Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Clerk Docs](https://clerk.com/docs)

### Internal Architecture
- System Design Documents
- API Specification
- Database Schema Documentation

## 🤝 Contributing

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```

### Code Review Process
1. Submit pull request
2. Automated tests run
3. Code review by team members
4. Merge after approval

---
*This document is automatically maintained by the Financial Management service repository.*
"""
        with open(DEV_DOC_FILE, "w", encoding="utf-8") as f:
            f.write(initial_content)
        print(f"✅ Created new developer documentation file: {DEV_DOC_FILE}")
        return
    
    # Read existing content
    with open(DEV_DOC_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update timestamp
    updated_content = content.replace(
        f"> **Last Updated:** {datetime.now().strftime('%B %Y')}",
        f"> **Last Updated:** {datetime.now().strftime('%B %Y')}"
    )
    
    # Add recent authentication section if not present
    if "## 🔐 Authentication Development" not in content:
        # Find Testing section and add auth development
        sections = updated_content.split("## 🧪 Testing")
        if len(sections) >= 2:
            auth_section = f"""

## 🔐 Authentication Development

### Testing Authenticated Requests
```python
# Backend test with auth
import pytest
from app.auth.middleware import create_test_token

def test_protected_endpoint(client):
    token = create_test_token(user_id="test-user", roles=["admin"])
    response = client.get("/api/v1/entities", headers={{"Authorization": f"Bearer {{token}}"}})
    assert response.status_code == 200
```

### Frontend Auth Testing
```typescript
// Mock Clerk auth in tests
import {{ mockClerk }} from '@/__tests__/mocks/clerk'

describe('Protected Component', () => {{
  beforeEach(() => {{
    mockClerk()
  }})
  
  // Test implementation
}})
```

### Recent Authentication Updates
- ✅ Integrated Clerk App 1 authentication
- ✅ Added JWT token validation middleware
- ✅ Implemented role-based access control
- ✅ Created protected route middleware
- ✅ Added frontend auth context providers

"""
            updated_content = sections[0] + auth_section + "## 🧪 Testing" + sections[1]
    
    # Write updated content
    with open(DEV_DOC_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print(f"✅ Updated developer documentation: {DEV_DOC_FILE}")

if __name__ == "__main__":
    main()