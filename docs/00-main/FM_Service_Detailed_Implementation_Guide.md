# Financial Management Service - Detailed Implementation Guide

**Version:** 1.0  
**Date:** December 21, 2025  
**Status:** Active Development  
**Last Updated:** December 21, 2025

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Database Design](#database-design)
4. [Service Architecture](#service-architecture)
5. [API Design](#api-design)
6. [Security Implementation](#security-implementation)
7. [Integration Implementation](#integration-implementation)
8. [Development Guidelines](#development-guidelines)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Guide](#deployment-guide)
11. [Performance Optimization](#performance-optimization)
12. [Monitoring & Logging](#monitoring--logging)
13. [UI/UX Development](#uiux-development)
14. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TrueVow Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Billing Module  │────────▶│   FM Service     │          │
│  │  (Separate)      │  Sync   │  (This Module)   │          │
│  └──────────────────┘         └──────────────────┘          │
│         │                              │                     │
│         │                              │                     │
│         ▼                              ▼                     │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ Billing DB   │              │   FM DB      │            │
│  │ (Isolated)   │              │ (Isolated)   │            │
│  └──────────────┘              └──────────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Service Isolation:** Complete separation from billing module
2. **Database Isolation:** Separate database with no direct access to billing data
3. **Security-First:** Finance-only access, encrypted communications
4. **Async-First:** Async/await throughout for performance
5. **Repository Pattern:** Data access abstraction layer
6. **Domain-Driven Design:** Service boundaries aligned with business domains

### Component Architecture

**Granular, Junior-Developer-Friendly Structure**

Each module is self-contained with predictable sub-folders. A junior developer can easily navigate to any component, page, route, script, or asset without searching through a "sea of code".

```
app/
├── modules/                          # All business modules (self-contained)
│   │
│   ├── ar_summary/                   # AR Summary Module
│   │   ├── pages/                    # UI pages/templates
│   │   │   ├── summary/
│   │   │   │   ├── ar_summary_list.html
│   │   │   │   └── ar_summary_detail.html
│   │   │   └── reports/
│   │   │       ├── ar_aging_report.html
│   │   │       └── ar_summary_report.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── ar_summary.py
│   │   │       └── ar_reports.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   ├── aging_calculator.py
│   │   │   │   └── currency_converter.py
│   │   │   ├── validators/
│   │   │   │   └── ar_validator.py
│   │   │   └── transformers/
│   │   │       └── billing_data_transformer.py
│   │   ├── services/
│   │   │   ├── ar_summary_service.py
│   │   │   ├── sync_service.py
│   │   │   └── report_service.py
│   │   ├── models/
│   │   │   └── ar_summary_model.py
│   │   ├── repositories/
│   │   │   └── ar_summary_repository.py
│   │   ├── schemas/
│   │   │   ├── ar_summary_schema.py
│   │   │   └── ar_report_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── ar_summary.css
│   │   │   ├── js/
│   │   │   │   └── ar_summary.js
│   │   │   └── images/
│   │   ├── utils/
│   │   │   └── ar_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_ar_summary_service.py
│   │       │   ├── test_sync_service.py
│   │       │   └── calculations/
│   │       │       └── test_aging_calculator.py
│   │       ├── integration/
│   │       │   └── test_ar_api.py
│   │       └── fixtures/
│   │           └── ar_fixtures.py
│   │
│   ├── accounts_payable/             # Accounts Payable Module
│   │   ├── pages/
│   │   │   ├── vendors/
│   │   │   │   ├── vendor_list.html
│   │   │   │   ├── vendor_detail.html
│   │   │   │   └── vendor_form.html
│   │   │   ├── invoices/
│   │   │   │   ├── invoice_list.html
│   │   │   │   ├── invoice_detail.html
│   │   │   │   └── invoice_form.html
│   │   │   └── payments/
│   │   │       ├── payment_list.html
│   │   │       ├── payment_detail.html
│   │   │       └── payment_form.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── vendors.py
│   │   │       ├── invoices.py
│   │   │       └── payments.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   ├── invoice_total_calculator.py
│   │   │   │   ├── tax_calculator.py
│   │   │   │   └── payment_allocator.py
│   │   │   ├── validators/
│   │   │   │   ├── vendor_validator.py
│   │   │   │   ├── invoice_validator.py
│   │   │   │   └── payment_validator.py
│   │   │   └── processors/
│   │   │       └── payment_processor.py
│   │   ├── services/
│   │   │   ├── vendor_service.py
│   │   │   ├── invoice_service.py
│   │   │   └── payment_service.py
│   │   ├── models/
│   │   │   ├── vendor_model.py
│   │   │   ├── invoice_model.py
│   │   │   └── payment_model.py
│   │   ├── repositories/
│   │   │   ├── vendor_repository.py
│   │   │   ├── invoice_repository.py
│   │   │   └── payment_repository.py
│   │   ├── schemas/
│   │   │   ├── vendor_schema.py
│   │   │   ├── invoice_schema.py
│   │   │   └── payment_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── accounts_payable.css
│   │   │   └── js/
│   │   │       └── accounts_payable.js
│   │   ├── utils/
│   │   │   └── ap_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_vendor_service.py
│   │       │   ├── test_invoice_service.py
│   │       │   ├── calculations/
│   │       │   │   └── test_tax_calculator.py
│   │       │   └── validators/
│   │       │       └── test_invoice_validator.py
│   │       ├── integration/
│   │       │   └── test_ap_api.py
│   │       └── fixtures/
│   │           └── ap_fixtures.py
│   │
│   ├── cash_flow/                    # Cash Flow Module
│   │   ├── pages/
│   │   │   ├── transactions/
│   │   │   │   ├── transaction_list.html
│   │   │   │   └── transaction_detail.html
│   │   │   ├── statements/
│   │   │   │   └── cash_flow_statement.html
│   │   │   └── forecasts/
│   │   │       └── cash_flow_forecast.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── transactions.py
│   │   │       ├── statements.py
│   │   │       └── forecasts.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   ├── cash_balance_calculator.py
│   │   │   │   └── forecast_calculator.py
│   │   │   └── validators/
│   │   │       └── transaction_validator.py
│   │   ├── services/
│   │   │   ├── transaction_service.py
│   │   │   ├── statement_service.py
│   │   │   └── forecast_service.py
│   │   ├── models/
│   │   │   └── cash_transaction_model.py
│   │   ├── repositories/
│   │   │   └── cash_flow_repository.py
│   │   ├── schemas/
│   │   │   ├── transaction_schema.py
│   │   │   └── statement_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── cash_flow.css
│   │   │   └── js/
│   │   │       └── cash_flow.js
│   │   ├── utils/
│   │   │   └── cash_flow_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_transaction_service.py
│   │       │   └── calculations/
│   │       │       └── test_forecast_calculator.py
│   │       └── integration/
│   │           └── test_cash_flow_api.py
│   │
│   ├── financial_reporting/          # Financial Reporting Module
│   │   ├── pages/
│   │   │   ├── pnl/
│   │   │   │   └── pnl_statement.html
│   │   │   ├── balance_sheet/
│   │   │   │   └── balance_sheet.html
│   │   │   └── reports/
│   │   │       ├── trial_balance.html
│   │   │       └── general_ledger.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── pnl.py
│   │   │       ├── balance_sheet.py
│   │   │       └── reports.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   ├── pnl_calculator.py
│   │   │   │   ├── balance_sheet_calculator.py
│   │   │   │   └── trial_balance_calculator.py
│   │   │   └── generators/
│   │   │       └── report_generator.py
│   │   ├── services/
│   │   │   ├── pnl_service.py
│   │   │   ├── balance_sheet_service.py
│   │   │   └── report_service.py
│   │   ├── models/
│   │   │   └── (uses shared models from other modules)
│   │   ├── repositories/
│   │   │   └── reporting_repository.py
│   │   ├── schemas/
│   │   │   ├── pnl_schema.py
│   │   │   └── balance_sheet_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── financial_reporting.css
│   │   │   └── js/
│   │   │       └── financial_reporting.js
│   │   ├── utils/
│   │   │   └── reporting_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_pnl_service.py
│   │       │   └── calculations/
│   │       │       └── test_pnl_calculator.py
│   │       └── integration/
│   │           └── test_reporting_api.py
│   │
│   ├── hr_payroll/                   # HR/Payroll Module
│   │   ├── pages/
│   │   │   ├── employees/
│   │   │   │   ├── employee_list.html
│   │   │   │   ├── employee_profile.html
│   │   │   │   └── employee_form.html
│   │   │   └── payroll/
│   │   │       ├── payroll_list.html
│   │   │       ├── payroll_detail.html
│   │   │       └── payroll_processing.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── employees.py
│   │   │       └── payroll.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   ├── salary_calculator.py
│   │   │   │   ├── tax_withholding_calculator.py
│   │   │   │   └── net_pay_calculator.py
│   │   │   ├── validators/
│   │   │   │   ├── employee_validator.py
│   │   │   │   └── payroll_validator.py
│   │   │   └── processors/
│   │   │       └── payroll_processor.py
│   │   ├── services/
│   │   │   ├── employee_service.py
│   │   │   └── payroll_service.py
│   │   ├── models/
│   │   │   ├── employee_model.py
│   │   │   └── payroll_record_model.py
│   │   ├── repositories/
│   │   │   ├── employee_repository.py
│   │   │   └── payroll_repository.py
│   │   ├── schemas/
│   │   │   ├── employee_schema.py
│   │   │   └── payroll_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── hr_payroll.css
│   │   │   └── js/
│   │   │       └── hr_payroll.js
│   │   ├── utils/
│   │   │   └── payroll_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_employee_service.py
│   │       │   ├── test_payroll_service.py
│   │       │   ├── calculations/
│   │       │   │   └── test_salary_calculator.py
│   │       │   └── validators/
│   │       │       └── test_employee_validator.py
│   │       ├── integration/
│   │       │   └── test_payroll_api.py
│   │       └── fixtures/
│   │           └── payroll_fixtures.py
│   │
│   ├── currency/                     # Currency Module
│   │   ├── pages/
│   │   │   ├── rates/
│   │   │   │   ├── exchange_rate_list.html
│   │   │   │   └── exchange_rate_history.html
│   │   │   └── conversion/
│   │   │       └── currency_converter.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── exchange_rates.py
│   │   │       └── conversion.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   └── currency_converter.py
│   │   │   └── validators/
│   │   │       └── currency_validator.py
│   │   ├── services/
│   │   │   ├── exchange_rate_service.py
│   │   │   └── conversion_service.py
│   │   ├── models/
│   │   │   └── exchange_rate_model.py
│   │   ├── repositories/
│   │   │   └── currency_repository.py
│   │   ├── schemas/
│   │   │   ├── exchange_rate_schema.py
│   │   │   └── conversion_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── currency.css
│   │   │   └── js/
│   │   │       └── currency.js
│   │   ├── utils/
│   │   │   └── currency_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_exchange_rate_service.py
│   │       │   └── calculations/
│   │       │       └── test_currency_converter.py
│   │       └── integration/
│   │           └── test_currency_api.py
│   │
│   ├── tax/                          # Tax Module
│   │   ├── pages/
│   │   │   ├── tables/
│   │   │   │   ├── tax_table_list.html
│   │   │   │   └── tax_table_form.html
│   │   │   └── reports/
│   │   │       └── tax_report.html
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── tax_tables.py
│   │   │       └── tax_calculations.py
│   │   ├── scripts/
│   │   │   ├── calculations/
│   │   │   │   └── tax_calculator.py
│   │   │   └── validators/
│   │   │       └── tax_validator.py
│   │   ├── services/
│   │   │   ├── tax_table_service.py
│   │   │   └── tax_calculation_service.py
│   │   ├── models/
│   │   │   └── tax_table_model.py
│   │   ├── repositories/
│   │   │   └── tax_repository.py
│   │   ├── schemas/
│   │   │   ├── tax_table_schema.py
│   │   │   └── tax_calculation_schema.py
│   │   ├── assets/
│   │   │   ├── css/
│   │   │   │   └── tax.css
│   │   │   └── js/
│   │   │       └── tax.js
│   │   ├── utils/
│   │   │   └── tax_helpers.py
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── test_tax_table_service.py
│   │       │   └── calculations/
│   │       │       └── test_tax_calculator.py
│   │       └── integration/
│   │           └── test_tax_api.py
│   │
│   └── bank_reconciliation/         # Bank Reconciliation Module
│       ├── pages/
│       │   ├── accounts/
│       │   │   ├── bank_account_list.html
│       │   │   └── bank_account_detail.html
│       │   ├── statements/
│       │   │   └── bank_statement_import.html
│       │   └── reconciliation/
│       │       └── reconciliation_detail.html
│       ├── api/
│       │   └── routes/
│       │       ├── bank_accounts.py
│       │       ├── statements.py
│       │       └── reconciliation.py
│       ├── scripts/
│       │   ├── calculations/
│       │   │   └── reconciliation_calculator.py
│       │   ├── validators/
│       │   │   └── statement_validator.py
│       │   └── processors/
│       │       └── statement_importer.py
│       ├── services/
│       │   ├── bank_account_service.py
│       │   ├── statement_service.py
│       │   └── reconciliation_service.py
│       ├── models/
│       │   ├── bank_account_model.py
│       │   ├── bank_statement_model.py
│       │   └── reconciliation_model.py
│       ├── repositories/
│       │   ├── bank_account_repository.py
│       │   └── reconciliation_repository.py
│       ├── schemas/
│       │   ├── bank_account_schema.py
│       │   └── reconciliation_schema.py
│       ├── assets/
│       │   ├── css/
│       │   │   └── bank_reconciliation.css
│       │   └── js/
│       │       └── bank_reconciliation.js
│       ├── utils/
│       │   └── reconciliation_helpers.py
│       └── tests/
│           ├── unit/
│           │   ├── test_bank_account_service.py
│           │   └── calculations/
│           │       └── test_reconciliation_calculator.py
│           └── integration/
│               └── test_reconciliation_api.py
│
├── core/                              # Shared core utilities
│   ├── config.py                      # Application configuration
│   ├── database.py                    # Database connection & session
│   ├── exceptions.py                  # Custom exceptions
│   ├── logging.py                     # Logging configuration
│   └── middleware.py                  # Shared middleware
│
├── auth/                              # Authentication & Authorization
│   ├── middleware.py                  # Auth middleware
│   ├── roles.py                       # Role definitions
│   ├── permissions.py                 # Permission checks
│   └── dependencies.py                # Auth dependencies
│
├── integrations/                      # External integrations
│   ├── billing_sync/
│   │   ├── sync_client.py
│   │   ├── sync_scheduler.py
│   │   └── data_transformer.py
│   └── currency_api/
│       ├── exchange_rate_client.py
│       └── rate_fetcher.py
│
└── shared/                            # Shared utilities across modules
    ├── models/
    │   ├── base_model.py              # Base model class
    │   └── audit_model.py             # Audit log model
    ├── repositories/
    │   └── base_repository.py         # Base repository class
    ├── schemas/
    │   └── base_schema.py             # Base schema class
    ├── utils/
    │   ├── date_helpers.py
    │   ├── currency_helpers.py
    │   └── validation_helpers.py
    └── constants/
        ├── currencies.py
        └── statuses.py
```

### Navigation Examples for Junior Developers

**Finding Employee Profile Page:**
```
app/modules/hr_payroll/pages/employees/employee_profile.html
```

**Finding Salary Calculator:**
```
app/modules/hr_payroll/scripts/calculations/salary_calculator.py
```

**Finding Payroll API Route:**
```
app/modules/hr_payroll/api/routes/payroll.py
```

**Finding Employee Validator:**
```
app/modules/hr_payroll/scripts/validators/employee_validator.py
```

**Finding Payroll Tests:**
```
app/modules/hr_payroll/tests/unit/calculations/test_salary_calculator.py
```

**Finding Invoice Tax Calculator:**
```
app/modules/accounts_payable/scripts/calculations/tax_calculator.py
```

**Finding AR Aging Report:**
```
app/modules/ar_summary/pages/reports/ar_aging_report.html
```

### Structure Benefits

1. **Predictable Location:** Every file type has a standard location
2. **Self-Contained Modules:** Each module has everything it needs
3. **Easy Navigation:** Junior developers can find files by type and purpose
4. **Clear Separation:** Pages, API, scripts, models, tests are clearly separated
5. **Scalable:** Easy to add new modules following the same pattern

### Folder Structure Principles

#### 1. Module-Based Organization
- Each business domain (AR, AP, Payroll, etc.) is a self-contained module
- All module-related code lives within that module's folder
- Modules are independent and can be developed/maintained separately

#### 2. Predictable Sub-Folders
Every module follows the same structure:
- **`pages/`** - UI pages/templates organized by feature
- **`api/routes/`** - API endpoints organized by resource
- **`scripts/`** - Business logic scripts organized by type:
  - `calculations/` - Calculation logic
  - `validators/` - Validation logic
  - `processors/` - Processing logic
  - `transformers/` - Data transformation
- **`services/`** - Service layer classes
- **`models/`** - Database models
- **`repositories/`** - Data access layer
- **`schemas/`** - Pydantic schemas for validation
- **`assets/`** - Static assets (CSS, JS, images)
- **`utils/`** - Module-specific utilities
- **`tests/`** - Tests organized by type (unit, integration, fixtures)

#### 3. File Naming Conventions
- **Pages:** `{feature}_{action}.html` (e.g., `employee_profile.html`)
- **Scripts:** `{purpose}_{type}.py` (e.g., `salary_calculator.py`)
- **API Routes:** `{resource}.py` (e.g., `payroll.py`)
- **Services:** `{resource}_service.py` (e.g., `payroll_service.py`)
- **Models:** `{resource}_model.py` (e.g., `employee_model.py`)
- **Repositories:** `{resource}_repository.py` (e.g., `payroll_repository.py`)
- **Schemas:** `{resource}_schema.py` (e.g., `payroll_schema.py`)
- **Tests:** `test_{resource}_{aspect}.py` (e.g., `test_salary_calculator.py`)

#### 4. Navigation Rules for Junior Developers

**To find a page:**
1. Identify the module (e.g., `hr_payroll`)
2. Go to `app/modules/{module}/pages/`
3. Navigate to the feature subfolder (e.g., `employees/`)
4. Find the page file

**To find a calculation script:**
1. Identify the module
2. Go to `app/modules/{module}/scripts/calculations/`
3. Find the calculator file

**To find an API route:**
1. Identify the module
2. Go to `app/modules/{module}/api/routes/`
3. Find the resource file

**To find a validator:**
1. Identify the module
2. Go to `app/modules/{module}/scripts/validators/`
3. Find the validator file

**To find tests:**
1. Identify the module
2. Go to `app/modules/{module}/tests/`
3. Navigate to `unit/` or `integration/`
4. Find the test file

#### 5. Benefits of This Structure

- **Zero Ambiguity:** Every file has exactly one logical location
- **Fast Navigation:** Junior developers can find files in seconds
- **Self-Documenting:** Folder structure explains the codebase
- **Consistent:** Same pattern across all modules
- **Maintainable:** Easy to add new features following the pattern
- **Testable:** Tests live next to the code they test

---

## 🛠️ Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.11+ | Core language |
| Framework | FastAPI | 0.104.1 | Web framework |
| ASGI Server | Uvicorn | 0.24.0 | ASGI server |
| Database | PostgreSQL | 14+ | Primary database |
| ORM | SQLAlchemy | 2.0.23 | Async ORM |
| Database Driver | asyncpg | 0.29.0 | Async PostgreSQL driver |
| Migrations | Alembic | 1.12.1 | Database migrations |
| Validation | Pydantic | 2.5.0 | Data validation |
| Authentication | python-jose | 3.3.0 | JWT handling |
| Password Hashing | passlib | 1.7.4 | Password security |
| HTTP Client | httpx | 0.25.2 | Async HTTP client |
| Currency | forex-python | 1.12 | Currency conversion |
| Logging | loguru | 0.7.2 | Logging framework |
| Testing | pytest | 7.4.3 | Testing framework |
| Code Quality | black, flake8, mypy | Latest | Code quality tools |

### Infrastructure

- **Database:** Supabase (PostgreSQL)
- **Hosting:** To be determined (AWS/Azure/GCP)
- **Containerization:** Docker (optional)
- **CI/CD:** To be determined

---

## 🗄️ Database Design

### Database Schema Overview

#### Core Tables

1. **ar_summary** - Accounts Receivable summary data
2. **vendors** - Vendor information
3. **ap_invoices** - Accounts Payable invoices
4. **ap_payments** - AP payments
5. **cash_transactions** - Cash flow transactions
6. **chart_of_accounts** - Chart of accounts
7. **journal_entries** - General journal entries
8. **employees** - Employee information
9. **payroll_records** - Payroll records
10. **exchange_rates** - Currency exchange rates
11. **tax_tables** - Tax rate tables
12. **bank_accounts** - Bank account information
13. **bank_statements** - Bank statement transactions
14. **reconciliations** - Bank reconciliation records
15. **audit_logs** - Audit trail

### Detailed Schema Design

#### AR Summary Table

```sql
CREATE TABLE ar_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    tenant_name VARCHAR(255) NOT NULL,
    invoice_number VARCHAR(100),
    invoice_date DATE NOT NULL,
    due_date DATE,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    amount_base_currency DECIMAL(15, 2) NOT NULL,
    exchange_rate DECIMAL(10, 6),
    status VARCHAR(50) NOT NULL, -- 'pending', 'paid', 'overdue', 'partial'
    days_overdue INTEGER DEFAULT 0,
    aging_bucket VARCHAR(20), -- '0-30', '31-60', '61-90', '90+'
    synced_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sync_batch_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_invoice_date (invoice_date),
    INDEX idx_status (status),
    INDEX idx_aging_bucket (aging_bucket)
);
```

#### Vendors Table

```sql
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_name VARCHAR(255) NOT NULL,
    vendor_code VARCHAR(50) UNIQUE,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    tax_id VARCHAR(100),
    payment_terms VARCHAR(50) DEFAULT 'Net 30', -- 'Net 15', 'Net 30', 'Net 60', etc.
    default_currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    INDEX idx_vendor_code (vendor_code),
    INDEX idx_is_active (is_active)
);
```

#### AP Invoices Table

```sql
CREATE TABLE ap_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(100) NOT NULL UNIQUE,
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    subtotal DECIMAL(15, 2) NOT NULL,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    total_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    amount_base_currency DECIMAL(15, 2) NOT NULL,
    exchange_rate DECIMAL(10, 6),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'paid', 'cancelled'
    payment_status VARCHAR(50) DEFAULT 'unpaid', -- 'unpaid', 'partial', 'paid'
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    notes TEXT,
    document_url TEXT, -- URL to attached document
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_invoice_date (invoice_date),
    INDEX idx_due_date (due_date),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status)
);
```

#### AP Invoice Line Items Table

```sql
CREATE TABLE ap_invoice_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES ap_invoices(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit_price DECIMAL(15, 2) NOT NULL,
    line_total DECIMAL(15, 2) NOT NULL,
    account_id UUID REFERENCES chart_of_accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(invoice_id, line_number)
);
```

#### AP Payments Table

```sql
CREATE TABLE ap_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_number VARCHAR(100) NOT NULL UNIQUE,
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL, -- 'check', 'wire', 'ach', 'credit_card'
    payment_reference VARCHAR(255), -- Check number, wire reference, etc.
    total_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    amount_base_currency DECIMAL(15, 2) NOT NULL,
    exchange_rate DECIMAL(10, 6),
    bank_account_id UUID REFERENCES bank_accounts(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'processed', 'cancelled'
    notes TEXT,
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_payment_date (payment_date),
    INDEX idx_status (status)
);
```

#### Payment Allocations Table

```sql
CREATE TABLE payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES ap_payments(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES ap_invoices(id),
    allocated_amount DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(payment_id, invoice_id)
);
```

#### Cash Transactions Table

```sql
CREATE TABLE cash_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'receipt', 'disbursement', 'transfer', 'other'
    category VARCHAR(100),
    description TEXT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    amount_base_currency DECIMAL(15, 2) NOT NULL,
    exchange_rate DECIMAL(10, 6),
    bank_account_id UUID REFERENCES bank_accounts(id),
    reference_number VARCHAR(255),
    related_entity_type VARCHAR(50), -- 'ar_collection', 'ap_payment', 'payroll', etc.
    related_entity_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_bank_account_id (bank_account_id)
);
```

#### Chart of Accounts Table

```sql
CREATE TABLE chart_of_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_code VARCHAR(50) NOT NULL UNIQUE,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL, -- 'asset', 'liability', 'equity', 'revenue', 'expense'
    parent_account_id UUID REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_account_code (account_code),
    INDEX idx_account_type (account_type),
    INDEX idx_parent_account_id (parent_account_id)
);
```

#### Journal Entries Table

```sql
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_number VARCHAR(100) NOT NULL UNIQUE,
    entry_date DATE NOT NULL,
    description TEXT,
    reference_number VARCHAR(255),
    is_posted BOOLEAN DEFAULT FALSE,
    posted_at TIMESTAMP WITH TIME ZONE,
    posted_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    INDEX idx_entry_date (entry_date),
    INDEX idx_is_posted (is_posted)
);
```

#### Journal Entry Lines Table

```sql
CREATE TABLE journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
    debit_amount DECIMAL(15, 2) DEFAULT 0,
    credit_amount DECIMAL(15, 2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CHECK (debit_amount >= 0 AND credit_amount >= 0),
    CHECK ((debit_amount > 0 AND credit_amount = 0) OR (debit_amount = 0 AND credit_amount > 0))
);
```

#### Employees Table

```sql
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    department VARCHAR(100),
    position VARCHAR(100),
    hire_date DATE NOT NULL,
    employment_status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'terminated'
    salary DECIMAL(15, 2),
    salary_currency VARCHAR(3) DEFAULT 'USD',
    pay_period VARCHAR(50) DEFAULT 'monthly', -- 'weekly', 'bi-weekly', 'monthly'
    tax_id VARCHAR(100),
    bank_account_number VARCHAR(255),
    bank_routing_number VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_employee_id (employee_id),
    INDEX idx_employment_status (employment_status)
);
```

#### Payroll Records Table

```sql
CREATE TABLE payroll_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_period_start DATE NOT NULL,
    payroll_period_end DATE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id),
    gross_pay DECIMAL(15, 2) NOT NULL,
    deductions DECIMAL(15, 2) DEFAULT 0,
    tax_withholdings DECIMAL(15, 2) DEFAULT 0,
    net_pay DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    amount_base_currency DECIMAL(15, 2) NOT NULL,
    exchange_rate DECIMAL(10, 6),
    payment_date DATE,
    payment_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processed', 'paid'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    INDEX idx_employee_id (employee_id),
    INDEX idx_payroll_period_start (payroll_period_start),
    INDEX idx_payment_status (payment_status)
);
```

#### Exchange Rates Table

```sql
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate DECIMAL(15, 6) NOT NULL,
    rate_date DATE NOT NULL,
    source VARCHAR(100), -- 'api', 'manual'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(from_currency, to_currency, rate_date),
    INDEX idx_rate_date (rate_date),
    INDEX idx_currencies (from_currency, to_currency)
);
```

#### Tax Tables Table

```sql
CREATE TABLE tax_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tax_type VARCHAR(50) NOT NULL, -- 'income', 'sales', 'vat', 'payroll'
    jurisdiction VARCHAR(100) NOT NULL, -- Country/State/Region
    tax_name VARCHAR(255) NOT NULL,
    rate DECIMAL(10, 4) NOT NULL, -- Percentage rate
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_tax_type (tax_type),
    INDEX idx_jurisdiction (jurisdiction),
    INDEX idx_effective_dates (effective_from, effective_to)
);
```

#### Bank Accounts Table

```sql
CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_name VARCHAR(255) NOT NULL,
    account_number VARCHAR(100),
    bank_name VARCHAR(255) NOT NULL,
    bank_routing_number VARCHAR(100),
    account_type VARCHAR(50) NOT NULL, -- 'checking', 'savings', 'money_market'
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    opening_balance DECIMAL(15, 2) DEFAULT 0,
    current_balance DECIMAL(15, 2) DEFAULT 0,
    last_reconciled_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_is_active (is_active)
);
```

#### Bank Statements Table

```sql
CREATE TABLE bank_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id),
    statement_date DATE NOT NULL,
    transaction_date DATE NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'debit', 'credit'
    reference_number VARCHAR(255),
    is_reconciled BOOLEAN DEFAULT FALSE,
    matched_transaction_id UUID, -- Links to cash_transactions or other transactions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_bank_account_id (bank_account_id),
    INDEX idx_statement_date (statement_date),
    INDEX idx_is_reconciled (is_reconciled)
);
```

#### Reconciliations Table

```sql
CREATE TABLE reconciliations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id),
    reconciliation_date DATE NOT NULL,
    statement_balance DECIMAL(15, 2) NOT NULL,
    book_balance DECIMAL(15, 2) NOT NULL,
    difference DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'discrepancy'
    notes TEXT,
    reconciled_by UUID,
    reconciled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_bank_account_id (bank_account_id),
    INDEX idx_reconciliation_date (reconciliation_date),
    INDEX idx_status (status)
);
```

#### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL, -- 'create', 'update', 'delete', 'view', 'export'
    entity_type VARCHAR(100) NOT NULL, -- 'ar_summary', 'ap_invoice', 'payment', etc.
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_entity_type (entity_type),
    INDEX idx_entity_id (entity_id),
    INDEX idx_timestamp (timestamp)
);
```

### Database Relationships

```
vendors (1) ──< (many) ap_invoices
ap_invoices (1) ──< (many) ap_invoice_line_items
ap_invoices (many) ──< (many) payment_allocations
ap_payments (1) ──< (many) payment_allocations
chart_of_accounts (1) ──< (many) chart_of_accounts (self-referencing)
journal_entries (1) ──< (many) journal_entry_lines
chart_of_accounts (1) ──< (many) journal_entry_lines
employees (1) ──< (many) payroll_records
bank_accounts (1) ──< (many) bank_statements
bank_accounts (1) ──< (many) reconciliations
```

---

## 🔧 Service Architecture

### Service Layer Pattern

Each service module follows a consistent pattern:

```python
# Example: accounts_payable/service.py structure

class AccountsPayableService:
    def __init__(self, repository: APRepository, currency_service: CurrencyService):
        self.repository = repository
        self.currency_service = currency_service
    
    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        # Business logic
        # Validation
        # Currency conversion
        # Repository call
        pass
    
    async def process_payment(self, payment_data: PaymentCreate) -> Payment:
        # Business logic
        # Allocation logic
        # Update invoice status
        # Repository call
        pass
```

### Repository Pattern

```python
# Example: repositories/base.py

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        # Implementation
        pass
    
    async def create(self, data: dict) -> T:
        # Implementation
        pass
    
    async def update(self, id: UUID, data: dict) -> T:
        # Implementation
        pass
    
    async def delete(self, id: UUID) -> bool:
        # Implementation
        pass
```

### Dependency Injection

```python
# Example: api/dependencies.py

async def get_ap_service(
    session: AsyncSession = Depends(get_db_session),
    currency_service: CurrencyService = Depends(get_currency_service)
) -> AccountsPayableService:
    repository = APRepository(session, APInvoice)
    return AccountsPayableService(repository, currency_service)
```

---

## 🌐 API Design

### API Structure

```
/api/v1/
├── /ar-summary
│   ├── GET    /                    # List AR summary
│   ├── GET    /{id}                # Get AR by ID
│   ├── GET    /aging               # Get AR aging report
│   └── POST   /sync                # Trigger manual sync
│
├── /accounts-payable
│   ├── /vendors
│   │   ├── GET    /                # List vendors
│   │   ├── POST   /                # Create vendor
│   │   ├── GET    /{id}            # Get vendor
│   │   ├── PUT    /{id}            # Update vendor
│   │   └── DELETE /{id}            # Delete vendor
│   ├── /invoices
│   │   ├── GET    /                # List invoices
│   │   ├── POST   /                # Create invoice
│   │   ├── GET    /{id}            # Get invoice
│   │   ├── PUT    /{id}            # Update invoice
│   │   ├── POST   /{id}/approve    # Approve invoice
│   │   └── GET    /aging           # Get AP aging report
│   └── /payments
│       ├── GET    /                # List payments
│       ├── POST   /                # Create payment
│       ├── GET    /{id}            # Get payment
│       └── POST   /{id}/process    # Process payment
│
├── /cash-flow
│   ├── GET    /transactions        # List transactions
│   ├── POST   /transactions        # Create transaction
│   ├── GET    /statement           # Get cash flow statement
│   └── GET    /forecast            # Get cash flow forecast
│
├── /financial-reporting
│   ├── GET    /pnl                 # Get P&L statement
│   ├── GET    /balance-sheet       # Get balance sheet
│   ├── GET    /trial-balance       # Get trial balance
│   └── GET    /general-ledger      # Get general ledger
│
├── /hr-payroll
│   ├── /employees
│   │   ├── GET    /                # List employees
│   │   ├── POST   /                # Create employee
│   │   └── GET    /{id}            # Get employee
│   └── /payroll
│       ├── GET    /                # List payroll records
│       ├── POST   /                # Process payroll
│       └── GET    /{id}            # Get payroll record
│
├── /currency
│   ├── GET    /rates               # Get exchange rates
│   ├── POST   /rates               # Create/update rate
│   ├── POST   /convert             # Convert currency
│   └── GET    /rates/history       # Get rate history
│
└── /tax
    ├── GET    /tables              # Get tax tables
    ├── POST   /tables              # Create tax table
    ├── POST   /calculate           # Calculate tax
    └── GET    /reports             # Get tax reports
```

### API Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2025-12-21T10:00:00Z"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2025-12-21T10:00:00Z"
}
```

---

## 🔐 Security Implementation

### Authentication Flow

1. User authenticates with JWT token
2. Token validated via `verify_fm_access` middleware
3. User permissions checked via `check_fm_permission`
4. Request processed if authorized

### Authorization Levels

```python
# Permission hierarchy
READ < WRITE < ADMIN

# Role-based access
finance_head: [read, write, admin]
regional_finance_manager: [read, write]
accountant: [read, write] (financial_management only)
```

### Data Encryption

- **At Rest:** Database-level encryption (Supabase)
- **In Transit:** TLS 1.3 for all API calls
- **Sensitive Fields:** Additional encryption for PII (future)

### Audit Logging

All financial transactions and user actions logged to `audit_logs` table with:
- User ID
- Action type
- Entity type and ID
- Old and new values
- Timestamp
- IP address
- User agent

---

## 🔌 Integration Implementation

### Billing Module Sync

#### Sync Architecture

```python
# integrations/billing_sync/sync_client.py

class BillingSyncClient:
    async def fetch_ar_summary(self, since: datetime) -> List[ARSummary]:
        # Fetch AR summary from billing module
        # Transform to FM format
        # Return list of AR summary records
        pass
    
    async def sync_ar_summary(self) -> SyncResult:
        # Get last sync timestamp
        # Fetch new/updated records
        # Store in FM database
        # Update sync status
        # Log sync operation
        pass
```

#### Sync Scheduler

```python
# integrations/billing_sync/sync_scheduler.py

class SyncScheduler:
    async def schedule_sync(self):
        # Run sync on schedule (hourly/daily)
        # Handle errors and retries
        # Send notifications on failure
        pass
```

#### Data Transformation

```python
# integrations/billing_sync/data_transformer.py

class DataTransformer:
    def transform_ar_summary(self, billing_data: dict) -> ARSummary:
        # Transform billing AR data to FM format
        # Calculate aging buckets
        # Convert currency if needed
        pass
```

### Currency Exchange Rate API

```python
# integrations/currency_api/exchange_rate_client.py

class ExchangeRateClient:
    async def fetch_latest_rates(self) -> Dict[str, float]:
        # Fetch latest exchange rates from API
        # Store in database
        # Return rates dictionary
        pass
    
    async def get_historical_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        date: date
    ) -> float:
        # Get historical exchange rate
        # Use cached if available
        # Fetch from API if needed
        pass
```

---

## 📝 Development Guidelines

### Code Style

- **Formatting:** Black (line length 100)
- **Linting:** Flake8
- **Type Checking:** MyPy
- **Imports:** isort

### Naming Conventions

- **Files:** snake_case (e.g., `accounts_payable.py`)
- **Classes:** PascalCase (e.g., `AccountsPayableService`)
- **Functions/Methods:** snake_case (e.g., `create_invoice`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `DEFAULT_CURRENCY`)
- **Variables:** snake_case (e.g., `invoice_data`)

### Async/Await Usage

- Always use async/await for I/O operations
- Use `asyncpg` for database operations
- Use `httpx` for HTTP requests
- Use `asyncio.gather()` for parallel operations

### Error Handling

```python
# Use custom exceptions
class FMServiceException(Exception):
    pass

class ValidationError(FMServiceException):
    pass

class NotFoundError(FMServiceException):
    pass

# Handle errors in API layer
try:
    result = await service.create_invoice(data)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

### Logging

```python
from loguru import logger

logger.info("Invoice created", invoice_id=invoice.id, vendor_id=vendor.id)
logger.error("Sync failed", error=str(e), sync_batch_id=batch_id)
```

### Database Transactions

```python
async with session.begin():
    invoice = await repository.create(invoice_data)
    await repository.create_line_items(line_items)
    # Transaction commits automatically on success
    # Rolls back on exception
```

---

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_services/
│   ├── test_repositories/
│   └── test_utils/
├── integration/
│   ├── test_api/
│   ├── test_integrations/
│   └── test_database/
└── fixtures/
    └── test_data.py
```

### Unit Tests

- Test individual functions/methods
- Mock external dependencies
- Target: 80%+ coverage

### Integration Tests

- Test API endpoints
- Test database operations
- Test service integrations
- Use test database

### Test Data

- Use factories for test data generation
- Use fixtures for common test scenarios
- Clean up test data after tests

### Example Test

```python
import pytest
from app.services.accounts_payable import AccountsPayableService

@pytest.mark.asyncio
async def test_create_invoice(test_db_session, mock_currency_service):
    service = AccountsPayableService(
        repository=APRepository(test_db_session),
        currency_service=mock_currency_service
    )
    
    invoice_data = InvoiceCreate(
        invoice_number="INV-001",
        vendor_id=uuid4(),
        invoice_date=date.today(),
        # ... other fields
    )
    
    invoice = await service.create_invoice(invoice_data)
    
    assert invoice.id is not None
    assert invoice.invoice_number == "INV-001"
```

---

## 🚀 Deployment Guide

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Billing Sync
BILLING_API_URL=https://billing-api.example.com
BILLING_API_KEY=your-api-key
SYNC_INTERVAL_HOURS=1

# Currency API
CURRENCY_API_URL=https://api.exchangerate-api.com
CURRENCY_API_KEY=your-api-key

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Create initial schema"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ⚡ Performance Optimization

### Database Optimization

- Use indexes on frequently queried columns
- Use connection pooling
- Use async queries
- Batch operations when possible
- Use database views for complex queries

### Caching Strategy

- Cache exchange rates (TTL: 1 hour)
- Cache tax tables (TTL: 24 hours)
- Cache frequently accessed reports
- Use Redis for distributed caching (future)

### Query Optimization

- Use `select_related` / `joinedload` to avoid N+1 queries
- Use pagination for large datasets
- Use database aggregation for reports
- Optimize slow queries with EXPLAIN ANALYZE

### Async Processing

- Use background tasks for long-running operations
- Use message queues for sync operations (future)
- Process reports asynchronously
- Send emails asynchronously

---

## 📊 Monitoring & Logging

### Logging Levels

- **DEBUG:** Detailed information for debugging
- **INFO:** General informational messages
- **WARNING:** Warning messages for potential issues
- **ERROR:** Error messages for failures
- **CRITICAL:** Critical errors requiring immediate attention

### Logging Format

```python
{
    "timestamp": "2025-12-21T10:00:00Z",
    "level": "INFO",
    "message": "Invoice created",
    "invoice_id": "uuid",
    "vendor_id": "uuid",
    "user_id": "uuid"
}
```

### Metrics to Monitor

- API response times
- Database query times
- Error rates
- Sync success/failure rates
- Currency conversion accuracy
- User activity

### Health Checks

```python
# GET /health
{
    "status": "healthy",
    "database": "connected",
    "sync_status": "up_to_date",
    "timestamp": "2025-12-21T10:00:00Z"
}
```

---

## 🎨 UI/UX Development

### UI Framework Decision

**Options:**
1. **Server-Side Templates (Jinja2)** - FastAPI with Jinja2 templates
2. **Separate Frontend (React/Vue)** - API-only backend, separate frontend app
3. **Hybrid** - Server-side for admin, API for future mobile apps

**Recommendation:** Start with **Server-Side Templates (Jinja2)** for MVP:
- Faster development for finance team
- Simpler deployment (single service)
- Can migrate to separate frontend later
- HTML files in `pages/` folders support this approach

### UI Technology Stack

**If Server-Side Templates:**
- **Templates:** Jinja2
- **CSS Framework:** Tailwind CSS or Bootstrap
- **JavaScript:** Vanilla JS or Alpine.js (lightweight)
- **Icons:** Heroicons or Font Awesome
- **Charts:** Chart.js or D3.js

**If Separate Frontend:**
- **Framework:** React or Vue.js
- **State Management:** Redux/Vuex or Zustand/Pinia
- **UI Library:** Material-UI, Ant Design, or Shadcn/ui
- **Build Tool:** Vite or Next.js
- **API Client:** Axios or Fetch API

### UI Development Milestones

#### Milestone 8 — UI/UX Foundation (1–2 weeks)
- Framework selection and setup
- Design system (colors, typography, spacing)
- Component library (buttons, forms, tables, modals)
- Layout system (header, sidebar, main content)
- Authentication UI (login, token refresh)
- Navigation structure
- Responsive breakpoints
- Accessibility foundation (WCAG 2.1 AA)

#### Milestone 9 — Core UI Modules (2–3 weeks)
- Dashboard with key metrics
- Journal Entry UI (create, list, detail, post, reverse)
- Chart of Accounts management (CRUD)
- Period management (generate, close, lock)
- Dimensions management
- Basic report previews

#### Milestone 10 — AR/AP UI Modules (2–3 weeks)
- AR Summary pages (list, detail, filters)
- AR Aging report UI
- AP Vendor management UI
- AP Invoice entry form (with line items)
- AP Payment processing UI
- AP Aging report UI
- Deferred revenue schedule viewer

#### Milestone 11 — Payroll UI Modules (2–3 weeks)
- Employee management (list, profile, form)
- Payroll run workflow UI (create → calculate → approve → post)
- Pay component management
- Commission plan configuration UI
- Bonus plan configuration UI
- Payroll export UI (WPS, CSV download)
- Payslip viewer

#### Milestone 12 — Treasury & Reconciliation UI (2–3 weeks)
- Bank account management UI
- Bank transaction import (CSV upload, preview)
- Bank reconciliation UI (matching interface, adjustments)
- FX conversion UI
- Transfer management UI
- Cash position dashboard

#### Milestone 13 — Reporting & Analytics UI (2–3 weeks)
- Financial reports (Trial Balance, P&L, Balance Sheet)
- Cash flow statement UI
- GL detail viewer (with filters, search)
- Report export (PDF, Excel)
- Custom report builder (basic)
- Dashboard with charts and KPIs

#### Milestone 14 — UI Polish & Integration (1–2 weeks)
- UI/UX refinements based on feedback
- Performance optimization (lazy loading, code splitting)
- Mobile responsiveness testing
- Accessibility audit and fixes
- Cross-browser testing
- User acceptance testing
- Help system and documentation

### UI Component Structure

Following the granular structure, UI components are organized by module:

```
app/modules/{module}/
├── pages/                    # UI pages/templates
│   ├── {feature}/
│   │   ├── {page}.html      # Page template
│   │   └── {page}_form.html # Form template
│   └── reports/
│       └── {report}.html    # Report template
├── assets/
│   ├── css/
│   │   └── {module}.css     # Module-specific styles
│   ├── js/
│   │   └── {module}.js      # Module-specific JavaScript
│   └── images/              # Module images
```

### UI Development Guidelines

#### Design Principles
- **Finance-Grade:** Professional, trustworthy appearance
- **Clarity:** Clear labels, helpful tooltips
- **Efficiency:** Keyboard shortcuts for power users
- **Accessibility:** WCAG 2.1 AA compliance
- **Responsive:** Works on desktop, tablet, mobile

#### Component Patterns
- **Forms:** Consistent validation, error display
- **Tables:** Sortable, filterable, paginated
- **Modals:** Confirmation dialogs for destructive actions
- **Loading States:** Clear feedback during operations
- **Error Handling:** User-friendly error messages

#### Accessibility Requirements
- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios (WCAG AA)
- Focus indicators
- ARIA labels where needed
- Form labels and error associations

### UI Testing Strategy

- **Visual Testing:** Screenshot comparisons
- **Accessibility Testing:** axe-core, WAVE
- **Cross-Browser Testing:** Chrome, Firefox, Safari, Edge
- **Responsive Testing:** Multiple screen sizes
- **User Testing:** Finance team feedback sessions

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors
- Check DATABASE_URL environment variable
- Verify database is accessible
- Check connection pool settings

#### Sync Failures
- Check billing API connectivity
- Verify API credentials
- Check sync logs for errors
- Verify data format compatibility

#### Currency Conversion Errors
- Check exchange rate API connectivity
- Verify rate data in database
- Check for missing historical rates

#### Performance Issues
- Check database query performance
- Review indexes
- Check connection pool size
- Review caching strategy

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

---

## 📚 Additional Resources

### Documentation
- FastAPI Documentation: https://fastapi.tiangolo.com
- SQLAlchemy Documentation: https://docs.sqlalchemy.org
- Alembic Documentation: https://alembic.sqlalchemy.org

### Code Examples
- See `examples/` directory (to be created)
- API documentation: `/docs` (Swagger UI)
- ReDoc documentation: `/redoc`

---

## 🔄 Document Maintenance

**Update Frequency:** This document should be updated:
- When architecture changes
- When new services are added
- When database schema changes
- When API changes
- When deployment process changes
- At least monthly for status updates

**Change Log:**
- **v1.1 (2025-12-21):** Added UI/UX development section and milestones
- **v1.0 (2025-12-21):** Initial implementation guide creation

---

**Document Owner:** Engineering Team  
**Reviewers:** Architecture, Security, DevOps  
**Approval Status:** Pending Approval
