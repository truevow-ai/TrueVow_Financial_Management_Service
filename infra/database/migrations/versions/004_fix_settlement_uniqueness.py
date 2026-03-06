"""Fix settlement uniqueness constraint

Revision ID: 004_fix_settlement_uniqueness
Revises: 003_billing_sync_batch
Create Date: 2026-01-27 13:00:00.000000

This migration fixes settlement uniqueness:
1. Drops single-column unique constraint on external_settlement_id
2. Adds composite unique constraint on (source, external_settlement_id) where external_settlement_id IS NOT NULL
3. This prevents duplicate settlements from same provider with same external ID
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '004_fix_settlement_uniqueness'
down_revision = '003_billing_sync_batch'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure external_settlement_id exists (table may have been created without it)
    op.execute("""
        ALTER TABLE treasury_settlement
        ADD COLUMN IF NOT EXISTS external_settlement_id VARCHAR(255);
    """)
    
    # Only apply uniqueness when both source and external_settlement_id exist (table may have different schema)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'treasury_settlement' AND column_name = 'source')
               AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'treasury_settlement' AND column_name = 'external_settlement_id') THEN
                DROP INDEX IF EXISTS treasury_settlement_external_settlement_id_key;
                DROP INDEX IF EXISTS ix_treasury_settlement_external_settlement_id;
                CREATE UNIQUE INDEX uq_settlement_source_external_id ON treasury_settlement(source, external_settlement_id) WHERE external_settlement_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS ix_treasury_settlement_external_settlement_id ON treasury_settlement(external_settlement_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Only revert when both columns exist (match upgrade conditional)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'treasury_settlement' AND column_name = 'source')
               AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'treasury_settlement' AND column_name = 'external_settlement_id') THEN
                DROP INDEX IF EXISTS uq_settlement_source_external_id;
                DROP INDEX IF EXISTS ix_treasury_settlement_external_settlement_id;
                ALTER TABLE treasury_settlement ADD CONSTRAINT treasury_settlement_external_settlement_id_key UNIQUE (external_settlement_id);
            END IF;
        EXCEPTION WHEN duplicate_object THEN
            NULL;  -- constraint already exists, ignore
        END $$;
    """)
