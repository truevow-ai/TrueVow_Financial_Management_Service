"""Add idempotency scope and source_key safety

Revision ID: 002_idempotency_source_key
Revises: 001_approval_workflow
Create Date: 2026-01-25 14:00:00.000000

This migration adds:
1. legal_entity_id and source_key to journal_entry for duplicate posting prevention
2. Updates idempotency_keys table with proper scope fields
3. Adds unique constraints and indexes for performance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '002_idempotency_source_key'
down_revision = '001_approval_workflow'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =====================================================
    # PART A: journal_entry table changes
    # =====================================================
    
    # 1. Add legal_entity_id column (nullable first, will backfill then make NOT NULL)
    op.add_column('journal_entry', 
        sa.Column('legal_entity_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # 2. Add source_key column (nullable - only enforce uniqueness when not null)
    op.add_column('journal_entry',
        sa.Column('source_key', sa.String(255), nullable=True)
    )
    
    # 3. Backfill legal_entity_id from book.legal_entity_id
    op.execute("""
        UPDATE journal_entry je
        SET legal_entity_id = b.legal_entity_id
        FROM book b
        WHERE je.book_id = b.id
        AND je.legal_entity_id IS NULL
    """)
    
    # 4. Backfill source_key for existing posted entries (if deterministically possible)
    # For posted entries without source_key, we'll set a deterministic value based on entry_id
    # This ensures existing posted entries have a source_key, but new ones must follow the pattern
    op.execute("""
        UPDATE journal_entry
        SET source_key = 'JE:POST:' || id::text
        WHERE status = 'POSTED'
        AND source_key IS NULL
        AND posted_at IS NOT NULL
    """)
    
    # 5. Make legal_entity_id NOT NULL after backfill
    op.alter_column('journal_entry', 'legal_entity_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )
    
    # 6. Add foreign key constraint for legal_entity_id
    op.create_foreign_key(
        'fk_journal_entry_legal_entity_id',
        'journal_entry', 'legal_entity',
        ['legal_entity_id'], ['id']
    )
    
    # 7. Add unique constraint on (legal_entity_id, book_id, source_key)
    # Using partial unique index to allow NULL source_key (for draft entries)
    op.execute("""
        CREATE UNIQUE INDEX uq_journal_entry_source_key 
        ON journal_entry(legal_entity_id, book_id, source_key)
        WHERE source_key IS NOT NULL
    """)
    
    # 8. Add indexes for performance
    op.create_index('ix_journal_entry_legal_entity_id', 'journal_entry', ['legal_entity_id'], unique=False)
    op.create_index('ix_journal_entry_source_key', 'journal_entry', ['source_key'], unique=False)
    op.create_index('ix_journal_entry_book_posted_at', 'journal_entry', ['book_id', 'posted_at'], unique=False)
    
    # =====================================================
    # PART B: idempotency_keys table changes
    # =====================================================
    
    # 1. Drop old unique constraint and indexes (IF EXISTS — table may have been created without them)
    op.execute("ALTER TABLE idempotency_keys DROP CONSTRAINT IF EXISTS uq_idempotency_keys_key_route")
    op.execute("DROP INDEX IF EXISTS ix_idempotency_keys_key")
    op.execute("DROP INDEX IF EXISTS ix_idempotency_keys_route")
    
    # 2. Add new scope columns (nullable first, will backfill)
    op.add_column('idempotency_keys',
        sa.Column('legal_entity_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('idempotency_keys',
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('idempotency_keys',
        sa.Column('endpoint_key', sa.String(255), nullable=True)
    )
    
    # 3. Backfill endpoint_key from route (before we drop route)
    # For existing records, we'll set a legacy value since we can't deterministically map old routes
    op.execute("""
        UPDATE idempotency_keys
        SET endpoint_key = COALESCE(route, 'LEGACY')
        WHERE endpoint_key IS NULL
    """)
    
    # 4. Rename existing columns to match new schema
    # key -> idempotency_key
    op.alter_column('idempotency_keys', 'key',
        new_column_name='idempotency_key'
    )
    
    # Now drop route column (replaced by endpoint_key)
    op.drop_column('idempotency_keys', 'route')
    
    # 5. Create idempotency_state enum
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'idempotency_state') THEN
                CREATE TYPE idempotency_state AS ENUM ('PENDING', 'COMPLETED', 'FAILED');
            END IF;
        END $$;
    """)
    
    # 6. Add new response tracking columns
    op.add_column('idempotency_keys',
        sa.Column('state', postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', name='idempotency_state', create_type=False), 
                  nullable=True, server_default='COMPLETED')  # Default existing records to COMPLETED
    )
    op.add_column('idempotency_keys',
        sa.Column('response_status', sa.Integer(), nullable=True)
    )
    op.add_column('idempotency_keys',
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('idempotency_keys',
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 7. Backfill state, response_status, and locked_at for existing records
    op.execute("""
        UPDATE idempotency_keys
        SET state = COALESCE(state, 'COMPLETED'),
            response_status = COALESCE(response_status, 200),
            locked_at = COALESCE(locked_at, created_at)
        WHERE state IS NULL OR response_status IS NULL OR locked_at IS NULL
    """)
    
    # 8. For existing records, we can't backfill legal_entity_id/book_id deterministically
    # Since idempotency_keys are meant to be temporary (for request replay), we'll:
    # Option A: Delete old records (safest - they're temporary anyway)
    # Option B: Set sentinel values (if you need to keep them for audit)
    # We'll use Option A - delete old records since they can't be properly scoped
    op.execute("""
        DELETE FROM idempotency_keys
        WHERE legal_entity_id IS NULL OR book_id IS NULL
    """)
    
    # 8. Make new columns NOT NULL (all records now have values or were deleted)
    op.alter_column('idempotency_keys', 'legal_entity_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )
    op.alter_column('idempotency_keys', 'book_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False
    )
    op.alter_column('idempotency_keys', 'endpoint_key',
        existing_type=sa.String(255),
        nullable=False
    )
    op.alter_column('idempotency_keys', 'response_status',
        existing_type=sa.Integer(),
        nullable=False
    )
    
    # 10. Add new unique constraint
    op.create_unique_constraint(
        'uq_idempotency_keys_scope',
        'idempotency_keys',
        ['legal_entity_id', 'book_id', 'endpoint_key', 'idempotency_key']
    )
    
    # 11. Add indexes for performance
    op.create_index('ix_idempotency_keys_legal_entity_id', 'idempotency_keys', ['legal_entity_id'], unique=False)
    op.create_index('ix_idempotency_keys_book_id', 'idempotency_keys', ['book_id'], unique=False)
    op.create_index('ix_idempotency_keys_endpoint_key', 'idempotency_keys', ['endpoint_key'], unique=False)
    op.create_index('ix_idempotency_keys_idempotency_key', 'idempotency_keys', ['idempotency_key'], unique=False)
    op.create_index('ix_idempotency_keys_actor_user_id', 'idempotency_keys', ['actor_user_id'], unique=False)
    
    # 10. Update table comment
    op.execute("COMMENT ON TABLE idempotency_keys IS 'Idempotency keys for write API idempotency - scoped by entity, book, endpoint'")
    
    # 13. Update column comments
    op.execute("COMMENT ON COLUMN journal_entry.legal_entity_id IS 'Legal entity ID for source_key uniqueness constraint'")
    op.execute("COMMENT ON COLUMN journal_entry.source_key IS 'Deterministic posting key to prevent duplicate postings (e.g., JE:POST:{entry_id})'")


def downgrade() -> None:
    # =====================================================
    # PART B: Revert idempotency_keys changes
    # =====================================================
    
    # Drop new indexes
    op.drop_index('ix_idempotency_keys_actor_user_id', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_idempotency_key', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_endpoint_key', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_book_id', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_legal_entity_id', table_name='idempotency_keys')
    
    # Drop new unique constraint
    op.drop_constraint('uq_idempotency_keys_scope', 'idempotency_keys', type_='unique')
    
    # Revert columns
    op.alter_column('idempotency_keys', 'locked_at', nullable=True)
    op.alter_column('idempotency_keys', 'state', nullable=True)
    op.alter_column('idempotency_keys', 'response_status', nullable=True)
    op.alter_column('idempotency_keys', 'endpoint_key', nullable=True)
    op.alter_column('idempotency_keys', 'book_id', nullable=True)
    op.alter_column('idempotency_keys', 'legal_entity_id', nullable=True)
    
    # Drop state enum
    op.execute("DROP TYPE IF EXISTS idempotency_state")
    
    # Add back route column
    op.add_column('idempotency_keys',
        sa.Column('route', sa.String(255), nullable=True)
    )
    op.execute("""
        UPDATE idempotency_keys
        SET route = endpoint_key
        WHERE route IS NULL
    """)
    op.alter_column('idempotency_keys', 'route', nullable=False)
    
    # Rename idempotency_key back to key
    op.alter_column('idempotency_keys', 'idempotency_key',
        new_column_name='key'
    )
    
    # Drop new columns
    op.drop_column('idempotency_keys', 'locked_at')
    op.drop_column('idempotency_keys', 'state')
    op.drop_column('idempotency_keys', 'actor_user_id')
    op.drop_column('idempotency_keys', 'response_status')
    op.drop_column('idempotency_keys', 'endpoint_key')
    op.drop_column('idempotency_keys', 'book_id')
    op.drop_column('idempotency_keys', 'legal_entity_id')
    
    # Restore old unique constraint
    op.create_unique_constraint('uq_idempotency_keys_key_route', 'idempotency_keys', ['key', 'route'])
    op.create_index('ix_idempotency_keys_route', 'idempotency_keys', ['route'], unique=False)
    op.create_index('ix_idempotency_keys_key', 'idempotency_keys', ['key'], unique=False)
    
    # =====================================================
    # PART A: Revert journal_entry changes
    # =====================================================
    
    # Drop indexes
    op.drop_index('ix_journal_entry_book_posted_at', table_name='journal_entry')
    op.drop_index('ix_journal_entry_source_key', table_name='journal_entry')
    op.drop_index('ix_journal_entry_legal_entity_id', table_name='journal_entry')
    
    # Drop unique constraint
    op.execute("DROP INDEX IF EXISTS uq_journal_entry_source_key")
    
    # Drop foreign key
    op.drop_constraint('fk_journal_entry_legal_entity_id', 'journal_entry', type_='foreignkey')
    
    # Drop columns
    op.drop_column('journal_entry', 'source_key')
    op.drop_column('journal_entry', 'legal_entity_id')
