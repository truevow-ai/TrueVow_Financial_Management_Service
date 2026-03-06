-- Create missing tables required by migrations

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
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_object_type ON audit_log(object_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_object_id ON audit_log(object_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);

-- Idempotency State Enum
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'idempotency_state') THEN
        CREATE TYPE idempotency_state AS ENUM ('PENDING', 'COMPLETED', 'FAILED');
    END IF;
END $$;

-- Idempotency Keys (matching migration 002 schema)
CREATE TABLE IF NOT EXISTS idempotency_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_entity_id UUID NOT NULL,
    book_id UUID NOT NULL,
    endpoint_key VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    state idempotency_state NOT NULL DEFAULT 'COMPLETED',
    response_status INTEGER NOT NULL,
    response_blob TEXT NOT NULL,
    actor_user_id UUID,
    locked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE(legal_entity_id, book_id, endpoint_key, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_legal_entity_id ON idempotency_keys(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_book_id ON idempotency_keys(book_id);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_endpoint_key ON idempotency_keys(endpoint_key);
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_idempotency_key ON idempotency_keys(idempotency_key);

-- Drop CS onboarding tables (not part of Financial Management)
DROP TABLE IF EXISTS cs_customer_onboarding_progress CASCADE;
DROP TABLE IF EXISTS cs_onboarding_calendar_integrations CASCADE;
DROP TABLE IF EXISTS cs_onboarding_communications CASCADE;
DROP TABLE IF EXISTS cs_onboarding_compliance_settings CASCADE;
DROP TABLE IF EXISTS cs_onboarding_firm_profile CASCADE;
DROP TABLE IF EXISTS cs_onboarding_milestone_completions CASCADE;
DROP TABLE IF EXISTS cs_onboarding_milestones CASCADE;
DROP TABLE IF EXISTS cs_onboarding_phone_config CASCADE;
DROP TABLE IF EXISTS cs_onboarding_sequences CASCADE;
DROP TABLE IF EXISTS cs_onboarding_step_completions CASCADE;
