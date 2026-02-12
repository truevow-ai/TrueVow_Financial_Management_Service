"""Add approval workflow fields and period close checklist

Revision ID: 001_approval_workflow
Revises: 
Create Date: 2026-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_approval_workflow'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create period_close_checklist table
    op.create_table(
        'period_close_checklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_code', sa.Enum('BANK_REC_DONE', 'REVREC_DONE', 'PAYROLL_POSTED', 'ROYALTY_POSTED', 'AR_AGING_READY', 'AP_AGING_READY', name='checklistitemcode'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETE', 'SKIPPED', name='checklistitemstatus'), nullable=False, server_default='PENDING'),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('computed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['period_id'], ['accounting_period.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period_id', 'item_code', name='uq_period_close_checklist_period_item')
    )
    op.execute("COMMENT ON TABLE period_close_checklist IS 'Period close checklist items'")
    op.create_index(op.f('ix_period_close_checklist_period_id'), 'period_close_checklist', ['period_id'], unique=False)
    op.create_index(op.f('ix_period_close_checklist_item_code'), 'period_close_checklist', ['item_code'], unique=False)
    
    # Note: Approval fields (submitted_by, submitted_at, approved_by, approved_at, rejected_by, rejected_at, decision_reason, row_version)
    # are already defined in the models for:
    # - accounting_period (already has these fields in model)
    # - payroll_run (already has these fields in model)
    # - reconciliation_adjustment_batch (already has these fields in model)
    # - royalty_calculation (already has these fields in model)
    # 
    # If these fields don't exist in the database yet, they will be added by autogenerate when you run:
    # alembic revision --autogenerate -m "Add missing approval fields"
    # 
    # This migration only creates the new period_close_checklist table.


def downgrade() -> None:
    # Drop period_close_checklist table
    op.drop_index(op.f('ix_period_close_checklist_item_code'), table_name='period_close_checklist')
    op.drop_index(op.f('ix_period_close_checklist_period_id'), table_name='period_close_checklist')
    op.drop_table('period_close_checklist')
    
    # Note: Approval fields are not dropped here as they may have been added by a separate migration
    # If you need to remove them, create a separate migration for that.
