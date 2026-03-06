-- =====================================================
-- Row-Level Audit Triggers
-- TrueVow Financial Management Service
-- =====================================================
-- PURPOSE
--   Every INSERT, UPDATE, and DELETE on every audited
--   business table appends one row to row_audit_log
--   preserving full before/after JSONB snapshots.
--
--   updated_by / updated_at only capture the *last*
--   editor.  row_audit_log captures *every* editor
--   in chronological order and can never be overwritten.
--
-- ACTOR IDENTITY
--   The trigger reads three PostgreSQL GUCs that the
--   application sets at the start of each transaction:
--
--     SET LOCAL app.current_user_id   = '<user_id>';
--     SET LOCAL app.current_user_role = '<role>';
--     SET LOCAL app.correlation_id    = '<uuid>';
--
--   SET LOCAL is transaction-scoped — automatically
--   cleared at COMMIT / ROLLBACK.  Safe for pgBouncer
--   transaction-mode pooling.
--
--   If a GUC is absent (e.g. background tasks, migration
--   scripts) actor columns are stored as NULL — the row
--   is still captured.
--
-- IDEMPOTENT
--   Safe to re-run; uses CREATE TABLE IF NOT EXISTS,
--   CREATE OR REPLACE FUNCTION, DROP TRIGGER IF EXISTS.
-- =====================================================


-- =====================================================
-- 1.  row_audit_log TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS row_audit_log (
    -- Identity
    id              BIGSERIAL       PRIMARY KEY,
    event_id        UUID            NOT NULL DEFAULT uuid_generate_v4(),

    -- What changed
    table_name      TEXT            NOT NULL,
    pk_id           TEXT,                           -- primary-key value of the changed row (TEXT covers UUID, int, string)
    operation       CHAR(1)         NOT NULL        -- 'I'=INSERT | 'U'=UPDATE | 'D'=DELETE
                        CHECK (operation IN ('I','U','D')),

    -- Who changed it
    actor_user_id   TEXT,                           -- GUC app.current_user_id
    actor_role      TEXT,                           -- GUC app.current_user_role
    correlation_id  TEXT,                           -- GUC app.correlation_id

    -- Row snapshots
    before_data     JSONB,                          -- OLD.*  (NULL on INSERT)
    after_data      JSONB,                          -- NEW.*  (NULL on DELETE)
    changed_columns TEXT[],                         -- columns whose value changed (UPDATE only)

    -- When
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT clock_timestamp()
    -- clock_timestamp() = wall-clock time inside the txn,
    -- unlike now() which freezes at txn start.
);

-- row_audit_log must never be subject to tenant RLS —
-- the trigger runs SECURITY DEFINER and must always write.
ALTER TABLE row_audit_log DISABLE ROW LEVEL SECURITY;

-- Make the table append-only for non-superusers
-- (service role can INSERT; nobody can UPDATE or DELETE)
REVOKE UPDATE, DELETE, TRUNCATE ON row_audit_log FROM PUBLIC;

-- Indexes optimised for the most common access patterns
CREATE INDEX IF NOT EXISTS idx_ral_table_pk   ON row_audit_log (table_name, pk_id);
CREATE INDEX IF NOT EXISTS idx_ral_table_time ON row_audit_log (table_name, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_ral_actor      ON row_audit_log (actor_user_id) WHERE actor_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ral_operation  ON row_audit_log (operation);
CREATE INDEX IF NOT EXISTS idx_ral_recorded   ON row_audit_log (recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_ral_correl     ON row_audit_log (correlation_id) WHERE correlation_id IS NOT NULL;

COMMENT ON TABLE  row_audit_log IS
    'Immutable, database-level audit trail.  One row per INSERT/UPDATE/DELETE '
    'on every audited business table.  Never update or delete rows here.';

COMMENT ON COLUMN row_audit_log.operation       IS '''I''=INSERT | ''U''=UPDATE | ''D''=DELETE';
COMMENT ON COLUMN row_audit_log.before_data     IS 'OLD row as JSONB; NULL on INSERT.';
COMMENT ON COLUMN row_audit_log.after_data      IS 'NEW row as JSONB; NULL on DELETE.';
COMMENT ON COLUMN row_audit_log.changed_columns IS 'Array of column names whose value changed (UPDATE only). NULL on INSERT/DELETE.';
COMMENT ON COLUMN row_audit_log.actor_user_id   IS 'From GUC app.current_user_id — set by the application per transaction.';
COMMENT ON COLUMN row_audit_log.correlation_id  IS 'From GUC app.correlation_id — matches X-Correlation-ID request header.';


-- =====================================================
-- 2.  TRIGGER FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION fn_row_audit_log()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER                     -- always runs as function owner; bypasses RLS on row_audit_log
SET search_path = public             -- prevents search_path injection
AS $$
DECLARE
    v_operation     CHAR(1);
    v_pk            TEXT;
    v_actor_user_id TEXT;
    v_actor_role    TEXT;
    v_correlation   TEXT;
    v_before        JSONB;
    v_after         JSONB;
    v_changed       TEXT[];
    v_key           TEXT;
BEGIN
    -- ------------------------------------------------
    -- 2a. Resolve operation code
    -- ------------------------------------------------
    v_operation := CASE TG_OP
        WHEN 'INSERT' THEN 'I'
        WHEN 'UPDATE' THEN 'U'
        ELSE               'D'
    END;

    -- ------------------------------------------------
    -- 2b. Read GUCs — fail-safe, never raise
    -- ------------------------------------------------
    v_actor_user_id := NULLIF(current_setting('app.current_user_id',  true), '');
    v_actor_role    := NULLIF(current_setting('app.current_user_role', true), '');
    v_correlation   := NULLIF(current_setting('app.correlation_id',    true), '');

    -- ------------------------------------------------
    -- 2c. Extract PK and serialise rows
    -- ------------------------------------------------
    IF TG_OP = 'DELETE' THEN
        v_pk      := (row_to_json(OLD) ->> 'id');
        v_before  := row_to_json(OLD)::JSONB;
        v_after   := NULL;
        v_changed := NULL;

    ELSIF TG_OP = 'INSERT' THEN
        v_pk      := (row_to_json(NEW) ->> 'id');
        v_before  := NULL;
        v_after   := row_to_json(NEW)::JSONB;
        v_changed := NULL;

    ELSE  -- UPDATE
        v_pk     := (row_to_json(NEW) ->> 'id');
        v_before := row_to_json(OLD)::JSONB;
        v_after  := row_to_json(NEW)::JSONB;

        -- Identify only the columns that actually changed value
        v_changed := ARRAY[]::TEXT[];
        FOR v_key IN
            SELECT key FROM jsonb_object_keys(v_after) AS t(key)
        LOOP
            IF (v_before ->> v_key) IS DISTINCT FROM (v_after ->> v_key) THEN
                v_changed := v_changed || v_key;
            END IF;
        END LOOP;

        -- Suppress pure no-op UPDATEs (e.g. ORM touch with no real change)
        IF array_length(v_changed, 1) IS NULL THEN
            RETURN NEW;
        END IF;
    END IF;

    -- ------------------------------------------------
    -- 2d. Append audit row — never raises; trigger must not
    --     block the originating transaction.
    -- ------------------------------------------------
    BEGIN
        INSERT INTO row_audit_log (
            table_name,     pk_id,         operation,
            actor_user_id,  actor_role,    correlation_id,
            before_data,    after_data,    changed_columns
        ) VALUES (
            TG_TABLE_NAME,  v_pk,          v_operation,
            v_actor_user_id, v_actor_role, v_correlation,
            v_before,       v_after,       v_changed
        );
    EXCEPTION WHEN others THEN
        -- Log to pg_log but never abort the caller's transaction.
        RAISE WARNING 'fn_row_audit_log: failed to write audit row for %.%: %',
            TG_TABLE_NAME, v_pk, SQLERRM;
    END;

    -- AFTER triggers: return value is ignored by Postgres,
    -- but convention is NEW for INSERT/UPDATE, OLD for DELETE.
    RETURN CASE TG_OP WHEN 'DELETE' THEN OLD ELSE NEW END;
END;
$$;

COMMENT ON FUNCTION fn_row_audit_log() IS
    'Generic AFTER INSERT OR UPDATE OR DELETE trigger function. '
    'Appends one row to row_audit_log per changed row. '
    'Actor context read from GUCs: app.current_user_id, app.current_user_role, app.correlation_id.';


-- =====================================================
-- 3.  ATTACH TRIGGERS TO ALL AUDITED TABLES
-- =====================================================
-- Uses a DO block + EXECUTE format() so adding a new
-- table only requires one line in the array.
-- The %I format specifier quotes identifiers safely.
-- =====================================================
DO $$
DECLARE
    t TEXT;
    audited_tables TEXT[] := ARRAY[
        -- Core / GL
        'legal_entity',
        'book',
        'dimension',
        'dimension_value',
        'gl_account',
        'gl_account_mapping',
        'accounting_period',
        'journal_entry',
        'journal_line',
        'journal_line_dimension',
        -- GL support
        'reconciliation_session',
        'reconciliation_match',
        'external_sync_cursor',
        'source_object_map',
        'treasury_sync_batch',
        -- AR / Revenue
        'ar_customer',
        'ar_invoice',
        'ar_invoice_line',
        'ar_payment',
        'ar_allocation',
        'revenue_schedule',
        'revenue_schedule_period',
        'billing_sync_batch',
        -- Payroll / HR
        'hr_employee',
        'hr_employee_bank',
        'pay_group',
        'pay_component_definition',
        'pay_component_assignment',
        'payroll_run',
        'payroll_run_item',
        'payroll_run_component_line',
        'payroll_payment_batch',
        'commission_plan',
        'commission_rule',
        'commission_ledger',
        'bonus_plan',
        'bonus_result',
        -- Intercompany
        'intercompany_transfer',
        'royalty_agreement',
        'royalty_calculation',
        'intercompany_balance',
        -- Treasury
        'bank_account',
        'bank_transaction',
        'settlement',
        'fx_conversion',
        'transfer',
        'sync_cursor',
        -- AP
        'ap_vendor',
        'ap_bill',
        'ap_bill_line',
        'ap_payment',
        'ap_allocation',
        'ap_withholding_profile'
        -- NOTE: row_audit_log, audit_log, idempotency_keys are intentionally
        -- EXCLUDED to prevent infinite recursion and unnecessary noise.
    ];
BEGIN
    FOREACH t IN ARRAY audited_tables LOOP
        -- Only attach if the table actually exists (guards against partial deployments)
        IF EXISTS (
            SELECT 1
            FROM   information_schema.tables
            WHERE  table_schema = 'public'
            AND    table_name   = t
        ) THEN
            EXECUTE format(
                'DROP   TRIGGER IF EXISTS trg_row_audit_%I ON %I;
                 CREATE TRIGGER          trg_row_audit_%I
                     AFTER INSERT OR UPDATE OR DELETE ON %I
                     FOR EACH ROW EXECUTE FUNCTION fn_row_audit_log();',
                t, t,   -- DROP
                t, t    -- CREATE
            );
            RAISE NOTICE 'row_audit trigger attached to: %', t;
        ELSE
            RAISE NOTICE 'row_audit trigger SKIPPED (table not found): %', t;
        END IF;
    END LOOP;
END $$;
