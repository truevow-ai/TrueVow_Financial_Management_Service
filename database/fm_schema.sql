-- =====================================================
-- TrueVow Financial Management Service - Database Schema
-- =====================================================
-- Database: TrueVow_Financial_Management_Service
-- Generated: 2026-01-24
-- Purpose: Complete schema for Financial Management database
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ENUMS (Idempotent - only create if not exists)
-- =====================================================

-- Book Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'book_type') THEN
        CREATE TYPE book_type AS ENUM ('ACCRUAL', 'CASH');
    END IF;
END $$;

-- Period Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'period_status') THEN
        CREATE TYPE period_status AS ENUM ('OPEN', 'SOFT_CLOSED', 'CLOSED', 'LOCKED');
    END IF;
END $$;

-- Account Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_type') THEN
        CREATE TYPE account_type AS ENUM (
            'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE',
            'AR', 'AP', 'CASH', 'DEFERRED_REVENUE',
            'OTHER_ASSET', 'OTHER_LIABILITY', 'OTHER_INCOME', 'OTHER_INCOME_EXPENSE', 'CONTRA_REVENUE'
        );
    END IF;
END $$;

-- Journal Entry Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'journal_entry_status') THEN
        CREATE TYPE journal_entry_status AS ENUM ('DRAFT', 'POSTED', 'REVERSED');
    END IF;
END $$;

-- Invoice Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoice_status') THEN
        CREATE TYPE invoice_status AS ENUM ('DRAFT', 'ISSUED', 'PAID', 'PARTIALLY_PAID', 'OVERDUE', 'CANCELLED', 'REFUNDED');
    END IF;
END $$;

-- Payment Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status') THEN
        CREATE TYPE payment_status AS ENUM ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED');
    END IF;
END $$;

-- Schedule Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'schedule_status') THEN
        CREATE TYPE schedule_status AS ENUM ('ACTIVE', 'COMPLETED', 'CANCELLED');
    END IF;
END $$;

-- Transaction Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_type') THEN
        CREATE TYPE transaction_type AS ENUM ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE', 'INTEREST', 'OTHER');
    END IF;
END $$;

-- Transfer Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transfer_type') THEN
        CREATE TYPE transfer_type AS ENUM ('INTERCOMPANY', 'INTRA_ENTITY', 'EXTERNAL');
    END IF;
END $$;

-- Reconciliation Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reconciliation_status') THEN
        CREATE TYPE reconciliation_status AS ENUM ('DRAFT', 'IN_PROGRESS', 'COMPLETED', 'CLOSED');
    END IF;
END $$;

-- Payroll Run Status
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payroll_run_status') THEN
        CREATE TYPE payroll_run_status AS ENUM ('DRAFT', 'CALCULATED', 'APPROVED', 'POSTED', 'PAID', 'CLOSED');
    END IF;
END $$;

-- Component Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'component_type') THEN
        CREATE TYPE component_type AS ENUM ('EARNING', 'DEDUCTION', 'EMPLOYER_CONTRIBUTION');
    END IF;
END $$;

-- Pay Frequency
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pay_frequency') THEN
        CREATE TYPE pay_frequency AS ENUM ('MONTHLY', 'BIWEEKLY', 'WEEKLY');
    END IF;
END $$;

-- Pay Day Rule
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pay_day_rule') THEN
        CREATE TYPE pay_day_rule AS ENUM ('LAST_BUSINESS_DAY', 'FIRST_BUSINESS_DAY', 'FIXED_DAY', 'MONTHLY_DAY_5');
    END IF;
END $$;

-- Employee Type
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'employee_type') THEN
        CREATE TYPE employee_type AS ENUM ('EMPLOYEE', 'CONTRACTOR', 'DIRECTOR');
    END IF;
END $$;

-- =====================================================
-- CORE TABLES
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
COMMENT ON TABLE legal_entity IS 'Legal entities (companies)';

-- Book
CREATE TABLE IF NOT EXISTS book (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_type book_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_book_legal_entity_id ON book(legal_entity_id);
COMMENT ON TABLE book IS 'Accounting books (ACCRUAL or CASH) per legal entity';

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
COMMENT ON TABLE dimension IS 'Dimensions (tag categories)';

-- Dimension Value
CREATE TABLE IF NOT EXISTS dimension_value (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dimension_code VARCHAR(50) NOT NULL REFERENCES dimension(code),
    value_code VARCHAR(50) NOT NULL,
    value_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_dimension_value_dimension_code ON dimension_value(dimension_code);
COMMENT ON TABLE dimension_value IS 'Values for each dimension';

-- GL Account
CREATE TABLE IF NOT EXISTS gl_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES book(id),
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type account_type NOT NULL,
    parent_account_id UUID REFERENCES gl_account(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_gl_account_book_id ON gl_account(book_id);
CREATE INDEX IF NOT EXISTS idx_gl_account_parent_account_id ON gl_account(parent_account_id);
COMMENT ON TABLE gl_account IS 'Chart of Accounts - GL accounts per book';

-- GL Account Mapping
CREATE TABLE IF NOT EXISTS gl_account_mapping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID NOT NULL REFERENCES book(id),
    map_key VARCHAR(100) NOT NULL,
    gl_account_id UUID NOT NULL REFERENCES gl_account(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(legal_entity_id, book_id, map_key)
);
CREATE INDEX IF NOT EXISTS idx_gl_account_mapping_legal_entity_id ON gl_account_mapping(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_gl_account_mapping_book_id ON gl_account_mapping(book_id);
COMMENT ON TABLE gl_account_mapping IS 'Mapping keys to GL accounts for system-generated postings';

-- Accounting Period
CREATE TABLE IF NOT EXISTS accounting_period (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES book(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_name VARCHAR(50) NOT NULL,
    status period_status NOT NULL DEFAULT 'OPEN',
    closed_by UUID,
    closed_at DATE,
    lock_reason VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(book_id, period_start)
);
CREATE INDEX IF NOT EXISTS idx_accounting_period_book_id ON accounting_period(book_id);
CREATE INDEX IF NOT EXISTS idx_accounting_period_status ON accounting_period(status);
COMMENT ON TABLE accounting_period IS 'Monthly accounting periods per book';

-- Journal Entry
CREATE TABLE IF NOT EXISTS journal_entry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES book(id),
    period_id UUID NOT NULL REFERENCES accounting_period(id),
    entry_number VARCHAR(100) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT,
    reference_number VARCHAR(255),
    status journal_entry_status NOT NULL DEFAULT 'DRAFT',
    source_service VARCHAR(50),
    source_type VARCHAR(100),
    source_id UUID,
    idempotency_key VARCHAR(255) UNIQUE,
    reversed_by_entry_id UUID REFERENCES journal_entry(id),
    reversal_reason TEXT,
    posted_by UUID,
    posted_at DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_journal_entry_book_id ON journal_entry(book_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_period_id ON journal_entry(period_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_entry_number ON journal_entry(entry_number);
CREATE INDEX IF NOT EXISTS idx_journal_entry_entry_date ON journal_entry(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entry_status ON journal_entry(status);
CREATE INDEX IF NOT EXISTS idx_journal_entry_idempotency_key ON journal_entry(idempotency_key);
COMMENT ON TABLE journal_entry IS 'Journal entries - immutable after posting';

-- Journal Line
CREATE TABLE IF NOT EXISTS journal_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entry(id),
    book_id UUID NOT NULL REFERENCES book(id),
    gl_account_id UUID NOT NULL REFERENCES gl_account(id),
    line_number INTEGER NOT NULL,
    debit_tc NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    credit_tc NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL,
    debit_fc NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    credit_fc NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    fx_rate NUMERIC(15, 6),
    fx_source VARCHAR(100),
    fx_timestamp TIMESTAMP WITH TIME ZONE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(journal_entry_id, line_number),
    CHECK (debit_tc >= 0 AND credit_tc >= 0),
    CHECK ((debit_tc > 0 AND credit_tc = 0) OR (debit_tc = 0 AND credit_tc > 0))
);
CREATE INDEX IF NOT EXISTS idx_journal_line_journal_entry_id ON journal_line(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_line_book_id ON journal_line(book_id);
CREATE INDEX IF NOT EXISTS idx_journal_line_gl_account_id ON journal_line(gl_account_id);
COMMENT ON TABLE journal_line IS 'Journal entry lines - must balance (debits == credits)';

-- Journal Line Dimension
CREATE TABLE IF NOT EXISTS journal_line_dimension (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_line_id UUID NOT NULL REFERENCES journal_line(id),
    dimension_value_id UUID NOT NULL REFERENCES dimension_value(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(journal_line_id, dimension_value_id)
);
CREATE INDEX IF NOT EXISTS idx_journal_line_dimension_journal_line_id ON journal_line_dimension(journal_line_id);
CREATE INDEX IF NOT EXISTS idx_journal_line_dimension_dimension_value_id ON journal_line_dimension(dimension_value_id);
COMMENT ON TABLE journal_line_dimension IS 'Dimensions (tags) attached to journal lines';

-- =====================================================
-- AR (ACCOUNTS RECEIVABLE) TABLES
-- =====================================================

-- AR Customer
CREATE TABLE IF NOT EXISTS ar_customer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    external_customer_id VARCHAR(255) UNIQUE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_code VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ar_customer_legal_entity_id ON ar_customer(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_ar_customer_external_customer_id ON ar_customer(external_customer_id);
COMMENT ON TABLE ar_customer IS 'AR customers mapped from Billing service';

-- AR Invoice
CREATE TABLE IF NOT EXISTS ar_invoice (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    ar_customer_id UUID NOT NULL REFERENCES ar_customer(id),
    external_invoice_id VARCHAR(255) UNIQUE NOT NULL,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE,
    total_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status invoice_status NOT NULL DEFAULT 'ISSUED',
    paid_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    outstanding_amount NUMERIC(15, 2) NOT NULL,
    description TEXT,
    external_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_legal_entity_id ON ar_invoice(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_ar_customer_id ON ar_invoice(ar_customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_external_invoice_id ON ar_invoice(external_invoice_id);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_invoice_number ON ar_invoice(invoice_number);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_invoice_date ON ar_invoice(invoice_date);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_due_date ON ar_invoice(due_date);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_status ON ar_invoice(status);
COMMENT ON TABLE ar_invoice IS 'AR invoices synced from Billing service';

-- AR Invoice Line
CREATE TABLE IF NOT EXISTS ar_invoice_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ar_invoice_id UUID NOT NULL REFERENCES ar_invoice(id),
    line_number INTEGER NOT NULL,
    description TEXT,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00,
    unit_price NUMERIC(15, 2) NOT NULL,
    line_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    service_start DATE,
    service_end DATE,
    is_deferrable BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(ar_invoice_id, line_number)
);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_line_ar_invoice_id ON ar_invoice_line(ar_invoice_id);
COMMENT ON TABLE ar_invoice_line IS 'AR invoice line items';

-- AR Payment
CREATE TABLE IF NOT EXISTS ar_payment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    ar_customer_id UUID NOT NULL REFERENCES ar_customer(id),
    external_payment_id VARCHAR(255) UNIQUE NOT NULL,
    payment_date DATE NOT NULL,
    payment_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_method VARCHAR(50),
    status payment_status NOT NULL DEFAULT 'COMPLETED',
    reference_number VARCHAR(255),
    description TEXT,
    external_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ar_payment_legal_entity_id ON ar_payment(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_ar_payment_ar_customer_id ON ar_payment(ar_customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_payment_external_payment_id ON ar_payment(external_payment_id);
CREATE INDEX IF NOT EXISTS idx_ar_payment_payment_date ON ar_payment(payment_date);
CREATE INDEX IF NOT EXISTS idx_ar_payment_status ON ar_payment(status);
COMMENT ON TABLE ar_payment IS 'AR payments synced from Billing service';

-- AR Allocation
CREATE TABLE IF NOT EXISTS ar_allocation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ar_payment_id UUID NOT NULL REFERENCES ar_payment(id),
    ar_invoice_id UUID NOT NULL REFERENCES ar_invoice(id),
    allocated_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    allocation_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(ar_payment_id, ar_invoice_id)
);
CREATE INDEX IF NOT EXISTS idx_ar_allocation_ar_payment_id ON ar_allocation(ar_payment_id);
CREATE INDEX IF NOT EXISTS idx_ar_allocation_ar_invoice_id ON ar_allocation(ar_invoice_id);
COMMENT ON TABLE ar_allocation IS 'Payment allocations to invoices';

-- Revenue Schedule
CREATE TABLE IF NOT EXISTS revenue_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID NOT NULL REFERENCES book(id),
    ar_invoice_id UUID NOT NULL REFERENCES ar_invoice(id),
    ar_invoice_line_id UUID NOT NULL REFERENCES ar_invoice_line(id),
    total_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    service_start DATE NOT NULL,
    service_end DATE NOT NULL,
    recognition_cadence VARCHAR(20) NOT NULL DEFAULT 'MONTHLY',
    status schedule_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_legal_entity_id ON revenue_schedule(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_book_id ON revenue_schedule(book_id);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_ar_invoice_id ON revenue_schedule(ar_invoice_id);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_ar_invoice_line_id ON revenue_schedule(ar_invoice_line_id);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_status ON revenue_schedule(status);
COMMENT ON TABLE revenue_schedule IS 'Revenue recognition schedules from invoice lines';

-- Revenue Schedule Period
CREATE TABLE IF NOT EXISTS revenue_schedule_period (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_schedule_id UUID NOT NULL REFERENCES revenue_schedule(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    recognition_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    is_recognized BOOLEAN NOT NULL DEFAULT FALSE,
    recognized_at DATE,
    journal_entry_id UUID REFERENCES journal_entry(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(revenue_schedule_id, period_start)
);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_period_revenue_schedule_id ON revenue_schedule_period(revenue_schedule_id);
CREATE INDEX IF NOT EXISTS idx_revenue_schedule_period_is_recognized ON revenue_schedule_period(is_recognized);
COMMENT ON TABLE revenue_schedule_period IS 'Monthly recognition periods within a schedule';

-- =====================================================
-- TREASURY TABLES
-- =====================================================

-- Bank Account
CREATE TABLE IF NOT EXISTS treasury_bank_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    account_name VARCHAR(255) NOT NULL,
    account_number VARCHAR(100),
    bank_name VARCHAR(255) NOT NULL,
    bank_code VARCHAR(50),
    currency VARCHAR(3) NOT NULL,
    account_type VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    wps_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    wps_agent_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_account_legal_entity_id ON treasury_bank_account(legal_entity_id);
COMMENT ON TABLE treasury_bank_account IS 'Bank accounts per legal entity';

-- Bank Transaction
CREATE TABLE IF NOT EXISTS treasury_bank_transaction (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank_account_id UUID NOT NULL REFERENCES treasury_bank_account(id),
    transaction_date DATE NOT NULL,
    value_date DATE,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    transaction_type transaction_type NOT NULL,
    description TEXT,
    reference_number VARCHAR(255),
    counterparty_name VARCHAR(255),
    counterparty_account VARCHAR(100),
    balance_after NUMERIC(15, 2),
    is_reconciled BOOLEAN NOT NULL DEFAULT FALSE,
    reconciliation_id UUID,
    external_id VARCHAR(255) UNIQUE,
    import_batch_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_bank_account_id ON treasury_bank_transaction(bank_account_id);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_transaction_date ON treasury_bank_transaction(transaction_date);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_transaction_type ON treasury_bank_transaction(transaction_type);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_is_reconciled ON treasury_bank_transaction(is_reconciled);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_external_id ON treasury_bank_transaction(external_id);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_import_batch_id ON treasury_bank_transaction(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_account_date ON treasury_bank_transaction(bank_account_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_transaction_account_reconciled ON treasury_bank_transaction(bank_account_id, is_reconciled);
COMMENT ON TABLE treasury_bank_transaction IS 'Bank statement transactions';

-- Transfer
CREATE TABLE IF NOT EXISTS treasury_transfer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    transfer_date DATE NOT NULL,
    transfer_type transfer_type NOT NULL,
    from_bank_account_id UUID NOT NULL REFERENCES treasury_bank_account(id),
    to_bank_account_id UUID REFERENCES treasury_bank_account(id),
    to_entity_id UUID REFERENCES legal_entity(id),
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    from_bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    to_bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    description TEXT,
    reference_number VARCHAR(255),
    external_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_treasury_transfer_legal_entity_id ON treasury_transfer(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_treasury_transfer_transfer_date ON treasury_transfer(transfer_date);
CREATE INDEX IF NOT EXISTS idx_treasury_transfer_transfer_type ON treasury_transfer(transfer_type);
CREATE INDEX IF NOT EXISTS idx_treasury_transfer_external_id ON treasury_transfer(external_id);
COMMENT ON TABLE treasury_transfer IS 'Cash transfers (intercompany, intra-entity, external)';

-- FX Conversion
CREATE TABLE IF NOT EXISTS treasury_fx_conversion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    conversion_date DATE NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    from_amount NUMERIC(15, 2) NOT NULL,
    to_amount NUMERIC(15, 2) NOT NULL,
    fx_rate NUMERIC(15, 6) NOT NULL,
    fx_source VARCHAR(100),
    bank_account_id UUID REFERENCES treasury_bank_account(id),
    bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    journal_entry_id UUID REFERENCES journal_entry(id),
    description TEXT,
    reference_number VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_treasury_fx_conversion_legal_entity_id ON treasury_fx_conversion(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_treasury_fx_conversion_conversion_date ON treasury_fx_conversion(conversion_date);
COMMENT ON TABLE treasury_fx_conversion IS 'FX conversions';

-- Settlement
CREATE TABLE IF NOT EXISTS treasury_settlement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    settlement_date DATE NOT NULL,
    settlement_type VARCHAR(50) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    bank_account_id UUID REFERENCES treasury_bank_account(id),
    bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    journal_entry_id UUID REFERENCES journal_entry(id),
    description TEXT,
    reference_number VARCHAR(255),
    external_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_treasury_settlement_legal_entity_id ON treasury_settlement(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_treasury_settlement_settlement_date ON treasury_settlement(settlement_date);
COMMENT ON TABLE treasury_settlement IS 'Settlements';

-- Sync Cursor
CREATE TABLE IF NOT EXISTS treasury_sync_cursor (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    bank_account_id UUID NOT NULL REFERENCES treasury_bank_account(id),
    cursor_value VARCHAR(255) NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(legal_entity_id, bank_account_id)
);
CREATE INDEX IF NOT EXISTS idx_treasury_sync_cursor_legal_entity_id ON treasury_sync_cursor(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_treasury_sync_cursor_bank_account_id ON treasury_sync_cursor(bank_account_id);
COMMENT ON TABLE treasury_sync_cursor IS 'Sync cursors for bank transaction imports';

-- Reconciliation Session
CREATE TABLE IF NOT EXISTS reconciliation_session (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank_account_id UUID NOT NULL REFERENCES treasury_bank_account(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    statement_ending_balance NUMERIC(15, 2) NOT NULL,
    statement_currency VARCHAR(3) NOT NULL,
    status reconciliation_status NOT NULL DEFAULT 'DRAFT',
    reconciled_by UUID,
    reconciled_at DATE,
    difference NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_reconciliation_session_bank_account_id ON reconciliation_session(bank_account_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_session_status ON reconciliation_session(status);
COMMENT ON TABLE reconciliation_session IS 'Bank reconciliation sessions';

-- Reconciliation Match
CREATE TABLE IF NOT EXISTS reconciliation_match (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reconciliation_session_id UUID NOT NULL REFERENCES reconciliation_session(id),
    bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    journal_entry_id UUID REFERENCES journal_entry(id),
    match_type VARCHAR(50) NOT NULL,
    match_confidence NUMERIC(5, 2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(reconciliation_session_id, bank_transaction_id)
);
CREATE INDEX IF NOT EXISTS idx_reconciliation_match_reconciliation_session_id ON reconciliation_match(reconciliation_session_id);
COMMENT ON TABLE reconciliation_match IS 'Matches between bank transactions and journal entries';

-- =====================================================
-- PAYROLL TABLES
-- =====================================================

-- Pay Group
CREATE TABLE IF NOT EXISTS pay_group (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    group_code VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    frequency pay_frequency NOT NULL DEFAULT 'MONTHLY',
    payroll_currency VARCHAR(3) NOT NULL,
    pay_day_rule pay_day_rule NOT NULL DEFAULT 'LAST_BUSINESS_DAY',
    wps_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_pay_group_legal_entity_id ON pay_group(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_pay_group_group_code ON pay_group(group_code);
COMMENT ON TABLE pay_group IS 'Pay groups for payroll processing';

-- HR Employee
CREATE TABLE IF NOT EXISTS hr_employee (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    employee_code VARCHAR(100) UNIQUE NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    employee_type employee_type NOT NULL DEFAULT 'EMPLOYEE',
    country VARCHAR(10) NOT NULL,
    location VARCHAR(50),
    pay_group_id UUID REFERENCES pay_group(id),
    currency VARCHAR(3) NOT NULL,
    hire_date DATE,
    termination_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    wps_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    labour_id VARCHAR(100),
    mol_id VARCHAR(100),
    iban VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_hr_employee_legal_entity_id ON hr_employee(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_hr_employee_employee_code ON hr_employee(employee_code);
CREATE INDEX IF NOT EXISTS idx_hr_employee_pay_group_id ON hr_employee(pay_group_id);
COMMENT ON TABLE hr_employee IS 'HR Employee master data';

-- HR Employee Bank
CREATE TABLE IF NOT EXISTS hr_employee_bank (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hr_employee_id UUID NOT NULL REFERENCES hr_employee(id),
    bank_name VARCHAR(255) NOT NULL,
    account_number VARCHAR(100) NOT NULL,
    iban VARCHAR(50),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_hr_employee_bank_hr_employee_id ON hr_employee_bank(hr_employee_id);
COMMENT ON TABLE hr_employee_bank IS 'Employee bank details';

-- Pay Component Definition
CREATE TABLE IF NOT EXISTS pay_component_definition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    component_code VARCHAR(50) NOT NULL,
    component_name VARCHAR(255) NOT NULL,
    component_type component_type NOT NULL,
    is_taxable BOOLEAN NOT NULL DEFAULT TRUE,
    affects_wps_net BOOLEAN NOT NULL DEFAULT TRUE,
    gl_map_key VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(legal_entity_id, component_code)
);
CREATE INDEX IF NOT EXISTS idx_pay_component_definition_legal_entity_id ON pay_component_definition(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_pay_component_definition_component_code ON pay_component_definition(component_code);
COMMENT ON TABLE pay_component_definition IS 'Pay component definitions (earnings, deductions, employer contributions)';

-- Pay Component Assignment
CREATE TABLE IF NOT EXISTS pay_component_assignment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hr_employee_id UUID NOT NULL REFERENCES hr_employee(id),
    pay_component_id UUID NOT NULL REFERENCES pay_component_definition(id),
    amount NUMERIC(15, 2),
    rate NUMERIC(10, 4),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE,
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(hr_employee_id, pay_component_id)
);
CREATE INDEX IF NOT EXISTS idx_pay_component_assignment_hr_employee_id ON pay_component_assignment(hr_employee_id);
CREATE INDEX IF NOT EXISTS idx_pay_component_assignment_pay_component_id ON pay_component_assignment(pay_component_id);
COMMENT ON TABLE pay_component_assignment IS 'Pay component assignments to employees';

-- Payroll Run
CREATE TABLE IF NOT EXISTS payroll_run (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID NOT NULL REFERENCES book(id),
    pay_group_id UUID NOT NULL REFERENCES pay_group(id),
    run_number VARCHAR(100) UNIQUE NOT NULL,
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    pay_date DATE NOT NULL,
    status payroll_run_status NOT NULL DEFAULT 'DRAFT',
    total_gross NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_deductions NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_net NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_employer_contrib NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL,
    approved_by UUID,
    approved_at DATE,
    posted_by UUID,
    posted_at DATE,
    journal_entry_id UUID REFERENCES journal_entry(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_payroll_run_legal_entity_id ON payroll_run(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_payroll_run_book_id ON payroll_run(book_id);
CREATE INDEX IF NOT EXISTS idx_payroll_run_pay_group_id ON payroll_run(pay_group_id);
CREATE INDEX IF NOT EXISTS idx_payroll_run_run_number ON payroll_run(run_number);
CREATE INDEX IF NOT EXISTS idx_payroll_run_pay_period_start ON payroll_run(pay_period_start);
CREATE INDEX IF NOT EXISTS idx_payroll_run_pay_date ON payroll_run(pay_date);
CREATE INDEX IF NOT EXISTS idx_payroll_run_status ON payroll_run(status);
COMMENT ON TABLE payroll_run IS 'Payroll runs - immutable after posting';

-- Payroll Run Item
CREATE TABLE IF NOT EXISTS payroll_run_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_run(id),
    hr_employee_id UUID NOT NULL REFERENCES hr_employee(id),
    gross_pay NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_deductions NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    net_pay NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    employer_contributions NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(payroll_run_id, hr_employee_id)
);
CREATE INDEX IF NOT EXISTS idx_payroll_run_item_payroll_run_id ON payroll_run_item(payroll_run_id);
CREATE INDEX IF NOT EXISTS idx_payroll_run_item_hr_employee_id ON payroll_run_item(hr_employee_id);
COMMENT ON TABLE payroll_run_item IS 'Payroll run items per employee';

-- Payroll Run Component Line
CREATE TABLE IF NOT EXISTS payroll_run_component_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_item_id UUID NOT NULL REFERENCES payroll_run_item(id),
    pay_component_id UUID NOT NULL REFERENCES pay_component_definition(id),
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    calculation_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_payroll_run_component_line_payroll_run_item_id ON payroll_run_component_line(payroll_run_item_id);
CREATE INDEX IF NOT EXISTS idx_payroll_run_component_line_pay_component_id ON payroll_run_component_line(pay_component_id);
COMMENT ON TABLE payroll_run_component_line IS 'Detailed component lines for payroll run items';

-- Payroll Payment Batch
CREATE TABLE IF NOT EXISTS payroll_payment_batch (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_run(id),
    batch_number VARCHAR(100) UNIQUE NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    export_data TEXT,
    exported_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_payroll_payment_batch_payroll_run_id ON payroll_payment_batch(payroll_run_id);
CREATE INDEX IF NOT EXISTS idx_payroll_payment_batch_batch_number ON payroll_payment_batch(batch_number);
COMMENT ON TABLE payroll_payment_batch IS 'Payment batch exports (WPS, CSV)';

-- Commission Plan
CREATE TABLE IF NOT EXISTS commission_plan (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    plan_name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_commission_plan_legal_entity_id ON commission_plan(legal_entity_id);
COMMENT ON TABLE commission_plan IS 'Commission plans';

-- Commission Rule
CREATE TABLE IF NOT EXISTS commission_rule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commission_plan_id UUID NOT NULL REFERENCES commission_plan(id),
    rule_name VARCHAR(255) NOT NULL,
    basis VARCHAR(50) NOT NULL,
    rate NUMERIC(10, 4),
    amount NUMERIC(15, 2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_commission_rule_commission_plan_id ON commission_rule(commission_plan_id);
COMMENT ON TABLE commission_rule IS 'Commission calculation rules';

-- Commission Ledger
CREATE TABLE IF NOT EXISTS commission_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hr_employee_id UUID NOT NULL REFERENCES hr_employee(id),
    commission_plan_id UUID NOT NULL REFERENCES commission_plan(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    basis_amount NUMERIC(15, 2) NOT NULL,
    commission_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_commission_ledger_hr_employee_id ON commission_ledger(hr_employee_id);
CREATE INDEX IF NOT EXISTS idx_commission_ledger_commission_plan_id ON commission_ledger(commission_plan_id);
COMMENT ON TABLE commission_ledger IS 'Commission ledger entries';

-- Bonus Plan
CREATE TABLE IF NOT EXISTS bonus_plan (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    plan_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_bonus_plan_legal_entity_id ON bonus_plan(legal_entity_id);
COMMENT ON TABLE bonus_plan IS 'Bonus plans';

-- Bonus Result
CREATE TABLE IF NOT EXISTS bonus_result (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bonus_plan_id UUID NOT NULL REFERENCES bonus_plan(id),
    hr_employee_id UUID NOT NULL REFERENCES hr_employee(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    bonus_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_bonus_result_bonus_plan_id ON bonus_result(bonus_plan_id);
CREATE INDEX IF NOT EXISTS idx_bonus_result_hr_employee_id ON bonus_result(hr_employee_id);
COMMENT ON TABLE bonus_result IS 'Bonus calculation results';

-- =====================================================
-- INTERCOMPANY TABLES
-- =====================================================

-- Intercompany Transfer
CREATE TABLE IF NOT EXISTS intercompany_transfer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    to_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    transfer_date DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    transfer_type VARCHAR(50),
    description TEXT,
    reference_number VARCHAR(255),
    from_bank_account_id UUID REFERENCES treasury_bank_account(id),
    to_bank_account_id UUID REFERENCES treasury_bank_account(id),
    from_bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    to_bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    from_entity_je_id UUID REFERENCES journal_entry(id),
    to_entity_je_id UUID REFERENCES journal_entry(id),
    is_reconciled BOOLEAN NOT NULL DEFAULT FALSE,
    reconciled_at DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_intercompany_transfer_from_entity_id ON intercompany_transfer(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_intercompany_transfer_to_entity_id ON intercompany_transfer(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_intercompany_transfer_transfer_date ON intercompany_transfer(transfer_date);
CREATE INDEX IF NOT EXISTS idx_intercompany_transfer_is_reconciled ON intercompany_transfer(is_reconciled);
COMMENT ON TABLE intercompany_transfer IS 'Intercompany transfers between entities';

-- Royalty Agreement
CREATE TABLE IF NOT EXISTS royalty_agreement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    to_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    agreement_name VARCHAR(255) NOT NULL,
    basis VARCHAR(50) NOT NULL,
    rate NUMERIC(10, 4),
    amount NUMERIC(15, 2),
    currency VARCHAR(3) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_royalty_agreement_from_entity_id ON royalty_agreement(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_royalty_agreement_to_entity_id ON royalty_agreement(to_entity_id);
COMMENT ON TABLE royalty_agreement IS 'Royalty agreements between entities';

-- Royalty Calculation
CREATE TABLE IF NOT EXISTS royalty_calculation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    royalty_agreement_id UUID NOT NULL REFERENCES royalty_agreement(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    basis_amount NUMERIC(15, 2) NOT NULL,
    royalty_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    journal_entry_id UUID REFERENCES journal_entry(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_royalty_calculation_royalty_agreement_id ON royalty_calculation(royalty_agreement_id);
COMMENT ON TABLE royalty_calculation IS 'Royalty calculations per period';

-- Intercompany Balance
CREATE TABLE IF NOT EXISTS intercompany_balance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    to_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    balance_date DATE NOT NULL,
    balance_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(from_entity_id, to_entity_id, balance_date)
);
CREATE INDEX IF NOT EXISTS idx_intercompany_balance_from_entity_id ON intercompany_balance(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_intercompany_balance_to_entity_id ON intercompany_balance(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_intercompany_balance_balance_date ON intercompany_balance(balance_date);
COMMENT ON TABLE intercompany_balance IS 'Intercompany balance snapshots';

-- =====================================================
-- EXTERNAL SYNC TABLES
-- =====================================================

-- External Sync Cursor
CREATE TABLE IF NOT EXISTS external_sync_cursor (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    source_service VARCHAR(50) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    cursor_value VARCHAR(255) NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(legal_entity_id, source_service, object_type)
);
CREATE INDEX IF NOT EXISTS idx_external_sync_cursor_legal_entity_id ON external_sync_cursor(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_external_sync_cursor_source_service ON external_sync_cursor(source_service);
COMMENT ON TABLE external_sync_cursor IS 'Sync cursors for replay-safe external integration';

-- Source Object Map
CREATE TABLE IF NOT EXISTS source_object_map (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    source_service VARCHAR(50) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    internal_id UUID NOT NULL,
    book_id UUID REFERENCES book(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(legal_entity_id, source_service, object_type, external_id)
);
CREATE INDEX IF NOT EXISTS idx_source_object_map_legal_entity_id ON source_object_map(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_source_object_map_source_service ON source_object_map(source_service);
CREATE INDEX IF NOT EXISTS idx_source_object_map_external_id ON source_object_map(external_id);
COMMENT ON TABLE source_object_map IS 'Mapping of external IDs to internal IDs for deduplication';

-- =====================================================
-- AP (ACCOUNTS PAYABLE) TABLES
-- =====================================================

-- AP Withholding Profile (must be created before ap_bill)
CREATE TABLE IF NOT EXISTS ap_withholding_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    profile_name VARCHAR(255) NOT NULL,
    withholding_type VARCHAR(50),
    withholding_rate NUMERIC(5, 2) NOT NULL,
    gl_account_id UUID NOT NULL REFERENCES gl_account(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ap_withholding_profile_legal_entity_id ON ap_withholding_profile(legal_entity_id);
COMMENT ON TABLE ap_withholding_profile IS 'AP withholding tax profiles (optional)';

-- AP Vendor
CREATE TABLE IF NOT EXISTS ap_vendor (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    vendor_code VARCHAR(100) UNIQUE NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(50),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    tax_id VARCHAR(100),
    payment_terms VARCHAR(100),
    default_currency VARCHAR(3) NOT NULL,
    bank_name VARCHAR(255),
    bank_account_number VARCHAR(100),
    iban VARCHAR(50),
    swift_code VARCHAR(50),
    address TEXT,
    country VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ap_vendor_legal_entity_id ON ap_vendor(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_ap_vendor_vendor_code ON ap_vendor(vendor_code);
COMMENT ON TABLE ap_vendor IS 'AP vendors (vendors, consultants, affiliates)';

-- AP Bill
CREATE TABLE IF NOT EXISTS ap_bill (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID NOT NULL REFERENCES book(id),
    ap_vendor_id UUID NOT NULL REFERENCES ap_vendor(id),
    bill_number VARCHAR(100) UNIQUE NOT NULL,
    bill_date DATE NOT NULL,
    due_date DATE,
    total_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    paid_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    outstanding_amount NUMERIC(15, 2) NOT NULL,
    description TEXT,
    reference_number VARCHAR(255),
    withholding_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    withholding_profile_id UUID REFERENCES ap_withholding_profile(id),
    journal_entry_id UUID REFERENCES journal_entry(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ap_bill_legal_entity_id ON ap_bill(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_ap_bill_book_id ON ap_bill(book_id);
CREATE INDEX IF NOT EXISTS idx_ap_bill_ap_vendor_id ON ap_bill(ap_vendor_id);
CREATE INDEX IF NOT EXISTS idx_ap_bill_bill_number ON ap_bill(bill_number);
CREATE INDEX IF NOT EXISTS idx_ap_bill_bill_date ON ap_bill(bill_date);
CREATE INDEX IF NOT EXISTS idx_ap_bill_due_date ON ap_bill(due_date);
CREATE INDEX IF NOT EXISTS idx_ap_bill_status ON ap_bill(status);
COMMENT ON TABLE ap_bill IS 'AP bills (vendor invoices)';

-- AP Bill Line
CREATE TABLE IF NOT EXISTS ap_bill_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ap_bill_id UUID NOT NULL REFERENCES ap_bill(id),
    line_number INTEGER NOT NULL,
    gl_account_id UUID NOT NULL REFERENCES gl_account(id),
    description TEXT,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00,
    unit_price NUMERIC(15, 2) NOT NULL,
    line_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(ap_bill_id, line_number)
);
CREATE INDEX IF NOT EXISTS idx_ap_bill_line_ap_bill_id ON ap_bill_line(ap_bill_id);
CREATE INDEX IF NOT EXISTS idx_ap_bill_line_gl_account_id ON ap_bill_line(gl_account_id);
COMMENT ON TABLE ap_bill_line IS 'AP bill line items';

-- AP Payment
CREATE TABLE IF NOT EXISTS ap_payment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID NOT NULL REFERENCES book(id),
    ap_vendor_id UUID NOT NULL REFERENCES ap_vendor(id),
    payment_number VARCHAR(100) UNIQUE NOT NULL,
    payment_date DATE NOT NULL,
    payment_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(255),
    bank_account_id UUID REFERENCES treasury_bank_account(id),
    bank_transaction_id UUID REFERENCES treasury_bank_transaction(id),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    approved_by UUID,
    approved_at DATE,
    processed_at DATE,
    description TEXT,
    journal_entry_id UUID REFERENCES journal_entry(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_ap_payment_legal_entity_id ON ap_payment(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_ap_payment_book_id ON ap_payment(book_id);
CREATE INDEX IF NOT EXISTS idx_ap_payment_ap_vendor_id ON ap_payment(ap_vendor_id);
CREATE INDEX IF NOT EXISTS idx_ap_payment_payment_number ON ap_payment(payment_number);
CREATE INDEX IF NOT EXISTS idx_ap_payment_payment_date ON ap_payment(payment_date);
CREATE INDEX IF NOT EXISTS idx_ap_payment_status ON ap_payment(status);
COMMENT ON TABLE ap_payment IS 'AP payments to vendors';

-- AP Allocation
CREATE TABLE IF NOT EXISTS ap_allocation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ap_payment_id UUID NOT NULL REFERENCES ap_payment(id),
    ap_bill_id UUID NOT NULL REFERENCES ap_bill(id),
    allocated_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    allocation_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(ap_payment_id, ap_bill_id)
);
CREATE INDEX IF NOT EXISTS idx_ap_allocation_ap_payment_id ON ap_allocation(ap_payment_id);
CREATE INDEX IF NOT EXISTS idx_ap_allocation_ap_bill_id ON ap_allocation(ap_bill_id);
COMMENT ON TABLE ap_allocation IS 'Payment allocations to bills';

-- =====================================================
-- AFFILIATE TABLES
-- =====================================================

-- Affiliate Partner
CREATE TABLE IF NOT EXISTS affiliate_partner (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    partner_code VARCHAR(100) UNIQUE NOT NULL,
    partner_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    payment_terms VARCHAR(100),
    default_currency VARCHAR(3) NOT NULL,
    bank_name VARCHAR(255),
    bank_account_number VARCHAR(100),
    iban VARCHAR(50),
    address TEXT,
    country VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_affiliate_partner_legal_entity_id ON affiliate_partner(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_partner_partner_code ON affiliate_partner(partner_code);
COMMENT ON TABLE affiliate_partner IS 'Affiliate partners';

-- Affiliate Agreement
CREATE TABLE IF NOT EXISTS affiliate_agreement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    affiliate_partner_id UUID NOT NULL REFERENCES affiliate_partner(id),
    agreement_name VARCHAR(255) NOT NULL,
    commission_type VARCHAR(50),
    commission_rate NUMERIC(10, 4),
    commission_amount NUMERIC(15, 2),
    payout_frequency VARCHAR(50),
    payout_threshold NUMERIC(15, 2),
    effective_from DATE NOT NULL,
    effective_to DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_affiliate_agreement_legal_entity_id ON affiliate_agreement(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_agreement_affiliate_partner_id ON affiliate_agreement(affiliate_partner_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_agreement_status ON affiliate_agreement(status);
COMMENT ON TABLE affiliate_agreement IS 'Affiliate agreements with commission terms';

-- Affiliate Earning Event
CREATE TABLE IF NOT EXISTS affiliate_earning_event (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    affiliate_partner_id UUID NOT NULL REFERENCES affiliate_partner(id),
    affiliate_agreement_id UUID NOT NULL REFERENCES affiliate_agreement(id),
    event_date DATE NOT NULL,
    earning_type VARCHAR(50),
    basis_amount NUMERIC(15, 2) NOT NULL,
    commission_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    source_id UUID,
    source_type VARCHAR(50),
    journal_entry_id UUID REFERENCES journal_entry(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_affiliate_earning_event_legal_entity_id ON affiliate_earning_event(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_earning_event_affiliate_partner_id ON affiliate_earning_event(affiliate_partner_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_earning_event_affiliate_agreement_id ON affiliate_earning_event(affiliate_agreement_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_earning_event_event_date ON affiliate_earning_event(event_date);
CREATE INDEX IF NOT EXISTS idx_affiliate_earning_event_status ON affiliate_earning_event(status);
COMMENT ON TABLE affiliate_earning_event IS 'Affiliate earning events (commission accruals)';

-- Affiliate Payout
CREATE TABLE IF NOT EXISTS affiliate_payout (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    affiliate_partner_id UUID NOT NULL REFERENCES affiliate_partner(id),
    payout_number VARCHAR(100) UNIQUE NOT NULL,
    payout_date DATE NOT NULL,
    payout_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    ap_payment_id UUID REFERENCES ap_payment(id),
    approved_by UUID,
    approved_at DATE,
    processed_at DATE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_affiliate_payout_legal_entity_id ON affiliate_payout(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_payout_affiliate_partner_id ON affiliate_payout(affiliate_partner_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_payout_payout_number ON affiliate_payout(payout_number);
CREATE INDEX IF NOT EXISTS idx_affiliate_payout_payout_date ON affiliate_payout(payout_date);
CREATE INDEX IF NOT EXISTS idx_affiliate_payout_status ON affiliate_payout(status);
COMMENT ON TABLE affiliate_payout IS 'Affiliate payouts (paid via AP)';

-- =====================================================
-- PAYROLL ADDITIONAL TABLES
-- =====================================================

-- Pay Rule Set
CREATE TABLE IF NOT EXISTS pay_rule_set (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    rule_set_name VARCHAR(255) NOT NULL,
    rule_set_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_pay_rule_set_legal_entity_id ON pay_rule_set(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_pay_rule_set_rule_set_code ON pay_rule_set(rule_set_code);
COMMENT ON TABLE pay_rule_set IS 'Pay rule sets for payroll calculation';

-- Pay Rule
CREATE TABLE IF NOT EXISTS pay_rule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pay_rule_set_id UUID NOT NULL REFERENCES pay_rule_set(id),
    rule_name VARCHAR(255) NOT NULL,
    rule_code VARCHAR(50) NOT NULL,
    rule_type VARCHAR(50),
    rule_expression TEXT,
    priority INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(pay_rule_set_id, rule_code)
);
CREATE INDEX IF NOT EXISTS idx_pay_rule_pay_rule_set_id ON pay_rule(pay_rule_set_id);
COMMENT ON TABLE pay_rule IS 'Pay rules within a rule set';

-- Statutory Contribution Rule
CREATE TABLE IF NOT EXISTS stat_contribution_rule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    country VARCHAR(10) NOT NULL,
    contribution_type VARCHAR(50) NOT NULL,
    employee_rate NUMERIC(5, 2) NOT NULL,
    employer_rate NUMERIC(5, 2) NOT NULL,
    salary_cap NUMERIC(15, 2),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(legal_entity_id, country, contribution_type, effective_from)
);
CREATE INDEX IF NOT EXISTS idx_stat_contribution_rule_legal_entity_id ON stat_contribution_rule(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_stat_contribution_rule_country ON stat_contribution_rule(country);
COMMENT ON TABLE stat_contribution_rule IS 'Statutory contribution rules (GPSSA, EOBI, Social Security)';

-- Tax Withholding Table
CREATE TABLE IF NOT EXISTS tax_withholding_table (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    country VARCHAR(10) NOT NULL,
    tax_year INTEGER NOT NULL,
    income_from NUMERIC(15, 2) NOT NULL,
    income_to NUMERIC(15, 2),
    tax_rate NUMERIC(5, 2) NOT NULL,
    fixed_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(legal_entity_id, country, tax_year, income_from)
);
CREATE INDEX IF NOT EXISTS idx_tax_withholding_table_legal_entity_id ON tax_withholding_table(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_tax_withholding_table_country ON tax_withholding_table(country);
CREATE INDEX IF NOT EXISTS idx_tax_withholding_table_tax_year ON tax_withholding_table(tax_year);
COMMENT ON TABLE tax_withholding_table IS 'Tax withholding tables (config-driven, not hardcoded)';

-- Payroll Export Template
CREATE TABLE IF NOT EXISTS payroll_export_template (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    template_name VARCHAR(255) NOT NULL,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    export_format VARCHAR(50) NOT NULL,
    template_config TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_payroll_export_template_legal_entity_id ON payroll_export_template(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_payroll_export_template_template_code ON payroll_export_template(template_code);
COMMENT ON TABLE payroll_export_template IS 'Payroll export templates (WPS, CSV, etc.)';

-- Payroll Liability Balance
CREATE TABLE IF NOT EXISTS payroll_liability_balance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID NOT NULL REFERENCES book(id),
    liability_type VARCHAR(50) NOT NULL,
    balance_date DATE NOT NULL,
    balance_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    gl_account_id UUID NOT NULL REFERENCES gl_account(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(legal_entity_id, book_id, liability_type, balance_date)
);
CREATE INDEX IF NOT EXISTS idx_payroll_liability_balance_legal_entity_id ON payroll_liability_balance(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_payroll_liability_balance_book_id ON payroll_liability_balance(book_id);
CREATE INDEX IF NOT EXISTS idx_payroll_liability_balance_balance_date ON payroll_liability_balance(balance_date);
COMMENT ON TABLE payroll_liability_balance IS 'Payroll liability balances (tax, contributions payable)';

-- =====================================================
-- AUDIT & IDEMPOTENCY TABLES
-- =====================================================

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID,
    role VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    object_type VARCHAR(100) NOT NULL,
    object_id UUID,
    before JSONB,
    after JSONB,
    reason TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_object_type ON audit_log(object_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_object_id ON audit_log(object_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_timestamp ON audit_log(actor_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_object_type_id ON audit_log(object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_timestamp ON audit_log(action, timestamp);
COMMENT ON TABLE audit_log IS 'Audit log for all mutations and critical operations';

-- Idempotency Keys
CREATE TABLE IF NOT EXISTS idempotency_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) UNIQUE NOT NULL,
    route VARCHAR(255) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    response_blob TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(key, route)
);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_key ON idempotency_keys(key);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_route ON idempotency_keys(route);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_created_at ON idempotency_keys(created_at);
COMMENT ON TABLE idempotency_keys IS 'Idempotency keys for write API idempotency';

-- =====================================================
-- END OF SCHEMA
-- =====================================================
