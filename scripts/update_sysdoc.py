#!/usr/bin/env python
"""Update System Documentation for TrueVow Financial Management Service."""

import os
import sys
from datetime import datetime

# External documentation path (universal for all repos)
DOC_PATH = r"C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation"

# Target system documentation file
SYS_DOC_FILE = os.path.join(DOC_PATH, "TrueVow-Financial-Management-System-Docs.md")

def main():
    """Update the system documentation with recent architectural changes."""
    
    # Check if documentation directory exists
    if not os.path.exists(DOC_PATH):
        print(f"❌ Documentation directory not found: {DOC_PATH}")
        sys.exit(1)
    
    # Create system documentation file if it doesn't exist
    if not os.path.exists(SYS_DOC_FILE):
        print(f"📝 Creating new system documentation file: {SYS_DOC_FILE}")
        initial_content = f"""# TrueVow Financial Management Service - System Documentation

> **Version:** 1.0
> **Last Updated:** {datetime.now().strftime('%B %Y')}
> **Status:** ✅ CORE INFRASTRUCTURE COMPLETE | 🔄 API ENDPOINTS ACTIVE

---

## 🏗️ System Architecture Overview

### High-Level Architecture

```mermaid
graph TD
    A[Next.js Frontend] --> B[Clerk Authentication]
    B --> C[FastAPI Backend]
    C --> D[PostgreSQL Database]
    C --> E[Redis Cache]
    F[External Services] --> C
```

## 🔌 API Endpoints

### Authentication
- **POST** `/api/v1/auth/login` - User authentication
- **POST** `/api/v1/auth/logout` - User logout
- **GET** `/api/v1/auth/me` - Current user info

### Legal Entities
- **GET** `/api/v1/entities` - List all legal entities
- **GET** `/api/v1/entities/{{entity_id}}` - Get specific entity
- **POST** `/api/v1/entities` - Create new entity *(admin only)*
- **PUT** `/api/v1/entities/{{entity_id}}` - Update entity *(admin only)*
- **DELETE** `/api/v1/entities/{{entity_id}}` - Delete entity *(admin only)*

### Books
- **GET** `/api/v1/entities/{{entity_id}}/books` - List entity books
- **GET** `/api/v1/books/{{book_id}}` - Get specific book
- **POST** `/api/v1/books` - Create new book *(admin only)*

### Core Modules
- **General Ledger** - Chart of accounts, journal entries, periods
- **Accounts Receivable** - Customer management, invoices, payments
- **Accounts Payable** - Vendor management, bills, payments
- **Treasury** - Bank accounts, transactions, reconciliations
- **Payroll** - Employee management, payroll runs, payments

## 🗄️ Database Schema

### Core Tables

#### Legal Entity
```sql
legal_entity (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(10) NOT NULL,
    functional_currency VARCHAR(3) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
)
```

#### Book
```sql
book (
    id UUID PRIMARY KEY,
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_type VARCHAR(20) NOT NULL, -- ACCRUAL or CASH
    name VARCHAR(255) NOT NULL,
    functional_currency VARCHAR(3) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
)
```

### Relationships
- One Legal Entity can have multiple Books
- Books contain Chart of Accounts
- Books contain Accounting Periods
- Books contain Journal Entries

## 🔐 Security Architecture

### Authentication Flow
1. User authenticates with Clerk
2. Clerk provides JWT token
3. Frontend stores token in localStorage
4. API client automatically adds Authorization header
5. Backend validates JWT and extracts user context

### Role-Based Access Control
- **FINANCE_ADMIN** - Full system access
- **ACCOUNTANT** - Read/write financial data
- **VIEWER** - Read-only access
- **SERVICE** - Integration access

### Protected Resources
- Legal entity creation/modification
- Book management
- Period closing operations
- Sensitive financial data

## 🚀 Deployment Architecture

### Development
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **Database:** Local PostgreSQL

### Production
- **Frontend:** Vercel/Next.js hosting
- **Backend:** Cloud hosting (AWS/Azure/GCP)
- **Database:** Managed PostgreSQL service
- **Cache:** Redis for session/cache storage

## 📊 Monitoring & Logging

### Application Logs
- Structured logging with correlation IDs
- Request/response logging
- Error tracking and alerting
- Performance metrics

### Health Checks
- **GET** `/health` - Basic health check
- **GET** `/metrics` - Prometheus metrics
- Database connectivity tests
- External service health checks

## 🔧 Configuration Management

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
CLERK_JWT_ISSUER=...

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
```

### Configuration Files
- `alembic.ini` - Database migrations
- `pytest.ini` - Test configuration
- `.env` - Environment variables
- `requirements.txt` - Python dependencies

## 🛠️ Development Workflow

### Local Setup
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up database and run migrations
4. Start backend: `uvicorn app.main:app --reload`
5. Start frontend: `cd frontend && pnpm dev`

### Testing
- Unit tests: `python -m pytest tests/`
- Integration tests: `python -m pytest tests/integration/`
- Frontend tests: `cd frontend && pnpm test`

### Code Quality
- Type checking: `mypy .`
- Linting: `ruff check .`
- Formatting: `black .`

---
*This document is automatically maintained by the Financial Management service repository.*
"""
        with open(SYS_DOC_FILE, "w", encoding="utf-8") as f:
            f.write(initial_content)
        print(f"✅ Created new system documentation file: {SYS_DOC_FILE}")
        return
    
    # Read existing content
    with open(SYS_DOC_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update timestamp
    updated_content = content.replace(
        f"> **Last Updated:** {datetime.now().strftime('%B %Y')}",
        f"> **Last Updated:** {datetime.now().strftime('%B %Y')}"
    )
    
    # Add recent API endpoints section if not present
    if "### Legal Entities" not in content:
        # Find API Endpoints section and add legal entities
        sections = updated_content.split("### Core Modules")
        if len(sections) >= 2:
            legal_entities_section = """

### Legal Entities
- **GET** `/api/v1/entities` - List all legal entities
- **GET** `/api/v1/entities/{entity_id}` - Get specific entity
- **POST** `/api/v1/entities` - Create new entity *(admin only)*
- **PUT** `/api/v1/entities/{entity_id}` - Update entity *(admin only)*
- **DELETE** `/api/v1/entities/{entity_id}` - Delete entity *(admin only)*

### Books
- **GET** `/api/v1/entities/{entity_id}/books` - List entity books
- **GET** `/api/v1/books/{book_id}` - Get specific book
- **POST** `/api/v1/books` - Create new book *(admin only)*

"""
            updated_content = sections[0] + legal_entities_section + "### Core Modules" + "".join(sections[1:])
    
    # Write updated content
    with open(SYS_DOC_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print(f"✅ Updated system documentation: {SYS_DOC_FILE}")

if __name__ == "__main__":
    main()