"""add_intercompany_balance_is_reconciled

Revision ID: 009_intercompany_balance_fix
Revises: 008_schema_gaps_fix
Create Date: 2026-03-02

Adds:
  - is_reconciled column to intercompany_balance
"""
from alembic import op


revision = "009_intercompany_balance_fix"
down_revision = "008_schema_gaps_fix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'intercompany_balance'
                  AND column_name = 'is_reconciled'
            ) THEN
                ALTER TABLE intercompany_balance
                    ADD COLUMN is_reconciled BOOLEAN NOT NULL DEFAULT FALSE;
                CREATE INDEX IF NOT EXISTS idx_intercompany_balance_is_reconciled
                    ON intercompany_balance (is_reconciled);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS idx_intercompany_balance_is_reconciled;
        ALTER TABLE intercompany_balance DROP COLUMN IF EXISTS is_reconciled;
    """)
