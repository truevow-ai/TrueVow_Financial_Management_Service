"""add_row_audit_triggers

Revision ID: 006_add_row_audit_triggers
Revises: 2e8a98e93966
Create Date: 2026-03-02

Problem solved
--------------
updated_by / updated_at are a point-in-time snapshot of the last editor only —
every previous editor is permanently lost.

Fix
---
A database-level row_audit_log table with an AFTER INSERT OR UPDATE OR DELETE
trigger (fn_row_audit_log) on every business table.

Every mutation appends one immutable row to row_audit_log that contains:
  - table_name, pk_id, operation (I/U/D)
  - before_data JSONB (OLD.*), after_data JSONB (NEW.*)
  - changed_columns TEXT[]  -- for UPDATE: which columns actually differed
  - actor_user_id, actor_role  -- from GUCs set by the application per-transaction
  - correlation_id              -- from GUC set by the application per-transaction
  - recorded_at TIMESTAMPTZ    -- clock_timestamp() (wall clock, not txn-start)

Actor identity is injected via PostgreSQL GUCs:
  SET LOCAL app.current_user_id   = '<id>';
  SET LOCAL app.current_user_role = '<role>';
  SET LOCAL app.correlation_id    = '<uuid>';

SET LOCAL is transaction-scoped and safe for pgBouncer transaction-mode pooling.
If GUCs are absent (migration scripts, background tasks), actor columns are NULL —
the row is still captured.

The trigger function runs SECURITY DEFINER so it can always INSERT into
row_audit_log regardless of RLS policies on the calling session.

row_audit_log itself has RLS disabled and UPDATE/DELETE revoked from PUBLIC
to ensure the table is effectively append-only.
"""
from alembic import op

# revision identifiers
revision = '006_add_row_audit_triggers'
down_revision = '2e8a98e93966'
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Full SQL inlined for reliability (no filesystem path dependency)
# ---------------------------------------------------------------------------

_UPGRADE_SQL = """
-- =====================================================
-- row_audit_log TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS row_audit_log (
    id              BIGSERIAL       PRIMARY KEY,
    event_id        UUID            NOT NULL DEFAULT uuid_generate_v4(),
    table_name      TEXT            NOT NULL,
    pk_id           TEXT,
    operation       CHAR(1)         NOT NULL CHECK (operation IN ('I','U','D')),
    actor_user_id   TEXT,
    actor_role      TEXT,
    correlation_id  TEXT,
    before_data     JSONB,
    after_data      JSONB,
    changed_columns TEXT[],
    recorded_at     TIMESTAMPTZ     NOT NULL DEFAULT clock_timestamp()
);

ALTER TABLE row_audit_log DISABLE ROW LEVEL SECURITY;
REVOKE UPDATE, DELETE, TRUNCATE ON row_audit_log FROM PUBLIC;

CREATE INDEX IF NOT EXISTS idx_ral_table_pk   ON row_audit_log (table_name, pk_id);
CREATE INDEX IF NOT EXISTS idx_ral_table_time ON row_audit_log (table_name, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_ral_actor      ON row_audit_log (actor_user_id) WHERE actor_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ral_operation  ON row_audit_log (operation);
CREATE INDEX IF NOT EXISTS idx_ral_recorded   ON row_audit_log (recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_ral_correl     ON row_audit_log (correlation_id) WHERE correlation_id IS NOT NULL;

COMMENT ON TABLE row_audit_log IS
    'Immutable, database-level audit trail.  One row per INSERT/UPDATE/DELETE '
    'on every audited business table.  Never update or delete rows here.';

COMMENT ON COLUMN row_audit_log.operation       IS '''I''=INSERT | ''U''=UPDATE | ''D''=DELETE';
COMMENT ON COLUMN row_audit_log.before_data     IS 'OLD row as JSONB; NULL on INSERT.';
COMMENT ON COLUMN row_audit_log.after_data      IS 'NEW row as JSONB; NULL on DELETE.';
COMMENT ON COLUMN row_audit_log.changed_columns IS 'Columns whose value changed (UPDATE only). NULL on INSERT/DELETE.';
COMMENT ON COLUMN row_audit_log.actor_user_id   IS 'From GUC app.current_user_id — set per transaction by the application.';
COMMENT ON COLUMN row_audit_log.correlation_id  IS 'From GUC app.correlation_id — matches X-Correlation-ID request header.';

-- =====================================================
-- TRIGGER FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION fn_row_audit_log()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $fn$
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
    v_operation := CASE TG_OP
        WHEN 'INSERT' THEN 'I'
        WHEN 'UPDATE' THEN 'U'
        ELSE               'D'
    END;

    v_actor_user_id := NULLIF(current_setting('app.current_user_id',  true), '');
    v_actor_role    := NULLIF(current_setting('app.current_user_role', true), '');
    v_correlation   := NULLIF(current_setting('app.correlation_id',    true), '');

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

        v_changed := ARRAY[]::TEXT[];
        FOR v_key IN
            SELECT key FROM jsonb_object_keys(v_after) AS t(key)
        LOOP
            IF (v_before ->> v_key) IS DISTINCT FROM (v_after ->> v_key) THEN
                v_changed := v_changed || v_key;
            END IF;
        END LOOP;

        -- Suppress no-op UPDATEs
        IF array_length(v_changed, 1) IS NULL THEN
            RETURN NEW;
        END IF;
    END IF;

    BEGIN
        INSERT INTO row_audit_log (
            table_name,      pk_id,         operation,
            actor_user_id,   actor_role,    correlation_id,
            before_data,     after_data,    changed_columns
        ) VALUES (
            TG_TABLE_NAME,   v_pk,          v_operation,
            v_actor_user_id, v_actor_role,  v_correlation,
            v_before,        v_after,       v_changed
        );
    EXCEPTION WHEN others THEN
        RAISE WARNING 'fn_row_audit_log: failed for %.%: %', TG_TABLE_NAME, v_pk, SQLERRM;
    END;

    RETURN CASE TG_OP WHEN 'DELETE' THEN OLD ELSE NEW END;
END;
$fn$;

COMMENT ON FUNCTION fn_row_audit_log() IS
    'Generic AFTER INSERT OR UPDATE OR DELETE trigger. '
    'Appends one row to row_audit_log. '
    'Actor context from GUCs: app.current_user_id, app.current_user_role, app.correlation_id.';

-- =====================================================
-- ATTACH TRIGGERS TO ALL AUDITED TABLES
-- =====================================================
DO $$
DECLARE
    t TEXT;
    audited_tables TEXT[] := ARRAY[
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
        'reconciliation_session',
        'reconciliation_match',
        'external_sync_cursor',
        'source_object_map',
        'treasury_sync_batch',
        'ar_customer',
        'ar_invoice',
        'ar_invoice_line',
        'ar_payment',
        'ar_allocation',
        'revenue_schedule',
        'revenue_schedule_period',
        'billing_sync_batch',
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
        'intercompany_transfer',
        'royalty_agreement',
        'royalty_calculation',
        'intercompany_balance',
        'bank_account',
        'bank_transaction',
        'settlement',
        'fx_conversion',
        'transfer',
        'sync_cursor',
        'ap_vendor',
        'ap_bill',
        'ap_bill_line',
        'ap_payment',
        'ap_allocation',
        'ap_withholding_profile'
    ];
BEGIN
    FOREACH t IN ARRAY audited_tables LOOP
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
                t, t,
                t, t
            );
        END IF;
    END LOOP;
END $$;
"""


_DOWNGRADE_SQL = """
-- Remove triggers from all audited tables
DO $$
DECLARE
    t TEXT;
    audited_tables TEXT[] := ARRAY[
        'legal_entity','book','dimension','dimension_value','gl_account',
        'gl_account_mapping','accounting_period','journal_entry','journal_line',
        'journal_line_dimension','reconciliation_session','reconciliation_match',
        'external_sync_cursor','source_object_map','treasury_sync_batch',
        'ar_customer','ar_invoice','ar_invoice_line','ar_payment','ar_allocation',
        'revenue_schedule','revenue_schedule_period','billing_sync_batch',
        'hr_employee','hr_employee_bank','pay_group','pay_component_definition',
        'pay_component_assignment','payroll_run','payroll_run_item',
        'payroll_run_component_line','payroll_payment_batch','commission_plan',
        'commission_rule','commission_ledger','bonus_plan','bonus_result',
        'intercompany_transfer','royalty_agreement','royalty_calculation',
        'intercompany_balance','bank_account','bank_transaction','settlement',
        'fx_conversion','transfer','sync_cursor','ap_vendor','ap_bill',
        'ap_bill_line','ap_payment','ap_allocation','ap_withholding_profile'
    ];
BEGIN
    FOREACH t IN ARRAY audited_tables LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = t
        ) THEN
            EXECUTE format('DROP TRIGGER IF EXISTS trg_row_audit_%I ON %I', t, t);
        END IF;
    END LOOP;
END $$;

DROP FUNCTION IF EXISTS fn_row_audit_log();
DROP TABLE  IF EXISTS row_audit_log;
"""


def upgrade() -> None:
    op.execute(_UPGRADE_SQL)


def downgrade() -> None:
    op.execute(_DOWNGRADE_SQL)
