"""Add metadata_json to idempotency_keys

Revision ID: 005_add_idempotency_metadata
Revises: 004_fix_settlement_uniqueness
Create Date: 2026-01-27 14:00:00.000000

This migration adds:
1. metadata_json column to idempotency_keys for correlation/audit (batch_id, cursor info, etc.)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '005_add_idempotency_metadata'
down_revision = '004_fix_settlement_uniqueness'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add metadata_json column for correlation data
    op.add_column('idempotency_keys',
        sa.Column('metadata_json', sa.Text(), nullable=True)
    )
    
    # Add comment
    op.execute("COMMENT ON COLUMN idempotency_keys.metadata_json IS 'JSON metadata for correlation/audit (e.g., batch_id, cursor_start, cursor_end for sync operations)'")


def downgrade() -> None:
    op.drop_column('idempotency_keys', 'metadata_json')
