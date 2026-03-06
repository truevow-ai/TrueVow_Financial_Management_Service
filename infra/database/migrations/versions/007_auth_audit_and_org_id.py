"""add_auth_audit_log_and_external_org_id

Revision ID: 007_auth_audit_and_org_id
Revises: 006_add_row_audit_triggers
Create Date: 2026-03-02

Changes
-------
1. auth_audit_log table
   Mandatory per TrueVow Security Contract v1 Section 9.
   Captures every auth event (auth_success, auth_failure, scope_rejected,
   permission_denied, permission_service_unavailable) per request.

2. legal_entity.external_org_id  TEXT  (nullable)
   Maps the Clerk org_id (canonical TEXT tenant identifier per Contract
   Section 1.1) to the FM service's internal legal_entity UUID.

   Usage: auth middleware looks up legal_entity by external_org_id = jwt.org_id
   to resolve the UUID used for RLS policies (app.current_tenant_id GUC).

   Column is nullable to avoid breaking existing rows; populate via
   data migration after deployment.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '007_auth_audit_and_org_id'
down_revision = '006_add_row_audit_triggers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1.  auth_audit_log                                                  #
    # ------------------------------------------------------------------ #
    op.create_table(
        'auth_audit_log',

        sa.Column('id',                 postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuid_generate_v4()'),
                  comment='Event UUID primary key.'),
        sa.Column('request_id',         postgresql.UUID(as_uuid=True), nullable=False,
                  comment='UUID generated at middleware entry for this request.'),
        sa.Column('event_type',         sa.String(60),  nullable=False,
                  comment='auth_success | auth_failure | scope_rejected | permission_denied | permission_service_unavailable'),
        sa.Column('tenant_id',          sa.Text,        nullable=True,
                  comment='Clerk org_id (TEXT) — canonical cross-service tenant identifier.'),
        sa.Column('clerk_user_id',      sa.String(255), nullable=True,
                  comment='Clerk sub claim (user_xxxx).'),
        sa.Column('scope',              sa.String(30),  nullable=True,
                  comment='JWT scope: internal | tenant.'),
        sa.Column('fm_role',            sa.String(60),  nullable=True,
                  comment='FM RBAC role at time of event.'),
        sa.Column('endpoint',           sa.String(500), nullable=True,
                  comment='Request path.'),
        sa.Column('method',             sa.String(10),  nullable=True,
                  comment='HTTP method.'),
        sa.Column('ip_address',         sa.String(45),  nullable=True,
                  comment='Client IP address.'),
        sa.Column('user_agent',         sa.Text,        nullable=True,
                  comment='User-Agent header.'),
        sa.Column('correlation_id',     sa.String(100), nullable=True,
                  comment='X-Correlation-ID header.'),
        sa.Column('permission_checked', sa.String(200), nullable=True,
                  comment='The resource:action permission evaluated.'),
        sa.Column('response_status',    sa.Integer,     nullable=True,
                  comment='HTTP response status code.'),
        sa.Column('details',            postgresql.JSONB, nullable=True,
                  comment='Structured details: error, role, etc.'),
        sa.Column('created_at',         sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'),
                  comment='UTC timestamp when the auth event was recorded.'),

        sa.PrimaryKeyConstraint('id'),
        comment=(
            'Auth audit log per Security Contract v1 Section 9. '
            'Append-only — never update or delete rows.'
        ),
    )

    # Indexes
    op.create_index('idx_aal_event_type',    'auth_audit_log', ['event_type'])
    op.create_index('idx_aal_tenant_id',     'auth_audit_log', ['tenant_id'])
    op.create_index('idx_aal_user_id',       'auth_audit_log', ['clerk_user_id'])
    op.create_index('idx_aal_created_at',    'auth_audit_log', ['created_at'])
    op.create_index('idx_aal_correlation',   'auth_audit_log', ['correlation_id'])
    op.create_index('idx_aal_tenant_time',   'auth_audit_log', ['tenant_id',     'created_at'])
    op.create_index('idx_aal_user_time',     'auth_audit_log', ['clerk_user_id', 'created_at'])
    op.create_index('idx_aal_event_time',    'auth_audit_log', ['event_type',    'created_at'])

    # Disable RLS — auth_audit_log must always be writable by the auth middleware
    op.execute("ALTER TABLE auth_audit_log DISABLE ROW LEVEL SECURITY;")
    # Append-only: revoke UPDATE/DELETE/TRUNCATE from PUBLIC
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON auth_audit_log FROM PUBLIC;")

    # ------------------------------------------------------------------ #
    # 2.  legal_entity.external_org_id                                    #
    # ------------------------------------------------------------------ #
    # Maps Clerk org_id (TEXT) → legal_entity UUID.
    # Used by auth middleware to resolve the UUID for RLS GUC injection.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'legal_entity'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name   = 'legal_entity'
                      AND column_name  = 'external_org_id'
                ) THEN
                    ALTER TABLE legal_entity
                        ADD COLUMN external_org_id TEXT;
                    COMMENT ON COLUMN legal_entity.external_org_id IS
                        'Clerk org_id (TEXT) — canonical cross-service tenant identifier. '
                        'Maps JWT org_id claim to this legal entity UUID.';
                    CREATE UNIQUE INDEX IF NOT EXISTS
                        idx_legal_entity_external_org_id
                        ON legal_entity (external_org_id)
                        WHERE external_org_id IS NOT NULL;
                END IF;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove external_org_id
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'legal_entity'
                  AND column_name  = 'external_org_id'
            ) THEN
                DROP INDEX IF EXISTS idx_legal_entity_external_org_id;
                ALTER TABLE legal_entity DROP COLUMN external_org_id;
            END IF;
        END $$;
    """)

    # Drop auth_audit_log
    op.execute("DROP INDEX IF EXISTS idx_aal_event_time;")
    op.execute("DROP INDEX IF EXISTS idx_aal_user_time;")
    op.execute("DROP INDEX IF EXISTS idx_aal_tenant_time;")
    op.execute("DROP INDEX IF EXISTS idx_aal_correlation;")
    op.execute("DROP INDEX IF EXISTS idx_aal_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_aal_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_aal_tenant_id;")
    op.execute("DROP INDEX IF EXISTS idx_aal_event_type;")
    op.drop_table('auth_audit_log')
