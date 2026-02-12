"""Add billing_sync_batch table

Revision ID: 003_billing_sync_batch
Revises: 002_idempotency_source_key
Create Date: 2026-01-27 12:00:00.000000

This migration adds:
1. billing_sync_batch table for tracking idempotent billing sync operations
2. Uses same SyncBatchStatus enum as treasury_sync_batch
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '003_billing_sync_batch'
down_revision = '002_idempotency_source_key'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum if not exists (shared by billing_sync_batch and treasury_sync_batch)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sync_batch_status') THEN
                CREATE TYPE sync_batch_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
            END IF;
        END $$;
    """)
    # Create billing_sync_batch table
    op.create_table(
        'billing_sync_batch',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
        sa.Column('legal_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_number', sa.String(100), nullable=False, unique=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='sync_batch_status', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('cursor_start', sa.String(255), nullable=True),
        sa.Column('cursor_end', sa.String(255), nullable=True),
        sa.Column('customers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invoices_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entity.id'], name='fk_billing_sync_batch_legal_entity_id'),
        sa.ForeignKeyConstraint(['book_id'], ['book.id'], name='fk_billing_sync_batch_book_id'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_billing_sync_batch_legal_entity_id', 'billing_sync_batch', ['legal_entity_id'], unique=False)
    op.create_index('ix_billing_sync_batch_book_id', 'billing_sync_batch', ['book_id'], unique=False)
    op.create_index('ix_billing_sync_batch_batch_number', 'billing_sync_batch', ['batch_number'], unique=True)
    op.create_index('ix_billing_sync_batch_status', 'billing_sync_batch', ['status'], unique=False)
    op.create_index('ix_billing_sync_batch_created_at', 'billing_sync_batch', ['created_at'], unique=False)
    
    # Add table comment
    op.execute("COMMENT ON TABLE billing_sync_batch IS 'Billing sync batches for idempotent sync operations'")


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_billing_sync_batch_created_at', table_name='billing_sync_batch')
    op.drop_index('ix_billing_sync_batch_status', table_name='billing_sync_batch')
    op.drop_index('ix_billing_sync_batch_batch_number', table_name='billing_sync_batch')
    op.drop_index('ix_billing_sync_batch_book_id', table_name='billing_sync_batch')
    op.drop_index('ix_billing_sync_batch_legal_entity_id', table_name='billing_sync_batch')
    
    # Drop table
    op.drop_table('billing_sync_batch')
