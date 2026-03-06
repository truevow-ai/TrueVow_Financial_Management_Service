-- =====================================================
-- TrueVow Financial Management - Base Schema (Enums + Tables Only)
-- =====================================================
-- Run this BEFORE migrations to create base structure
-- Migrations will handle idempotency_keys and other schema changes
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ENUMS (Idempotent - only create if not exists)
-- =====================================================

-- Book Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booktype') THEN
        CREATE TYPE booktype AS ENUM ('ACCRUAL', 'CASH');
    END IF;
END $$;

-- Period Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodstatus') THEN
        CREATE TYPE periodstatus AS ENUM ('OPEN', 'SOFT_CLOSED', 'CLOSED', 'LOCKED');
    END IF;
END $$;

-- Account Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'accounttype') THEN
        CREATE TYPE accounttype AS ENUM (
            'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE',
            'AR', 'AP', 'CASH', 'DEFERRED_REVENUE',
            'OTHER_ASSET', 'OTHER_LIABILITY', 'OTHER_INCOME', 'OTHER_INCOME_EXPENSE', 'CONTRA_REVENUE'
        );
    END IF;
END $$;

-- Journal Entry Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'journalentrystatus') THEN
        CREATE TYPE journalentrystatus AS ENUM ('DRAFT', 'POSTED', 'REVERSED');
    END IF;
END $$;

-- Invoice Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoicestatus') THEN
        CREATE TYPE invoicestatus AS ENUM ('DRAFT', 'ISSUED', 'PAID', 'PARTIALLY_PAID', 'OVERDUE', 'CANCELLED', 'REFUNDED');
    END IF;
END $$;

-- Payment Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentstatus') THEN
        CREATE TYPE paymentstatus AS ENUM ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED');
    END IF;
END $$;

-- Schedule Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'schedulestatus') THEN
        CREATE TYPE schedulestatus AS ENUM ('ACTIVE', 'COMPLETED', 'CANCELLED');
    END IF;
END $$;

-- Transaction Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
        CREATE TYPE transactiontype AS ENUM ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE', 'INTEREST', 'OTHER');
    END IF;
END $$;

-- Transfer Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transfertype') THEN
        CREATE TYPE transfertype AS ENUM ('INTERCOMPANY', 'INTRA_ENTITY', 'EXTERNAL');
    END IF;
END $$;

-- Reconciliation Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reconciliationstatus') THEN
        CREATE TYPE reconciliationstatus AS ENUM ('DRAFT', 'IN_PROGRESS', 'COMPLETED', 'CLOSED');
    END IF;
END $$;

-- Payroll Run Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payrollrunstatus') THEN
        CREATE TYPE payrollrunstatus AS ENUM ('DRAFT', 'CALCULATED', 'APPROVED', 'POSTED', 'PAID', 'CLOSED');
    END IF;
END $$;

-- Component Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'componenttype') THEN
        CREATE TYPE componenttype AS ENUM ('EARNING', 'DEDUCTION', 'EMPLOYER_CONTRIBUTION');
    END IF;
END $$;

-- Pay Frequency
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payfrequency') THEN
        CREATE TYPE payfrequency AS ENUM ('MONTHLY', 'BIWEEKLY', 'WEEKLY');
    END IF;
END $$;

-- Pay Day Rule
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paydayrule') THEN
        CREATE TYPE paydayrule AS ENUM ('LAST_BUSINESS_DAY', 'FIRST_BUSINESS_DAY', 'FIXED_DAY', 'MONTHLY_DAY_5');
    END IF;
END $$;

-- Employee Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'employeetype') THEN
        CREATE TYPE employeetype AS ENUM ('EMPLOYEE', 'CONTRACTOR', 'DIRECTOR');
    END IF;
END $$;

-- =====================================================
-- CORE TABLES (Minimal - only what's needed for seeding)
-- =====================================================

-- Legal Entity
CREATE TABLE IF NOT EXISTS legal_entity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(10) NOT NULL,
    functional_currency VARCHAR(3) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_legal_entity_code ON legal_entity(code);

-- Book
CREATE TABLE IF NOT EXISTS book (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_type booktype NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_book_legal_entity_id ON book(legal_entity_id);

-- Dimension
CREATE TABLE IF NOT EXISTS dimension (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_dimension_code ON dimension(code);

-- Dimension Value
CREATE TABLE IF NOT EXISTS dimension_value (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dimension_code VARCHAR(50) NOT NULL REFERENCES dimension(code),
    value_code VARCHAR(50) NOT NULL,
    value_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(dimension_code, value_code)
);
CREATE INDEX IF NOT EXISTS idx_dimension_value_dimension_code ON dimension_value(dimension_code);

-- GL Account
CREATE TABLE IF NOT EXISTS gl_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES book(id),
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type accounttype NOT NULL,
    parent_account_id UUID REFERENCES gl_account(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(book_id, account_code)
);
CREATE INDEX IF NOT EXISTS idx_gl_account_book_id ON gl_account(book_id);
CREATE INDEX IF NOT EXISTS idx_gl_account_account_code ON gl_account(account_code);

-- Accounting Period
CREATE TABLE IF NOT EXISTS accounting_period (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES book(id),
    period_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status periodstatus NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(book_id, period_name)
);
CREATE INDEX IF NOT EXISTS idx_accounting_period_book_id ON accounting_period(book_id);
CREATE INDEX IF NOT EXISTS idx_accounting_period_start_date ON accounting_period(start_date);

-- =====================================================
-- NOTE: Other tables will be created by migrations
-- idempotency_keys table will be created by migration 002
-- =====================================================
