"""Row Audit Log Model

Read-only SQLAlchemy mapping for the row_audit_log table.

row_audit_log is populated exclusively by the fn_row_audit_log() database
trigger — the application NEVER writes to it directly.  This model exists
only to let services query the audit history.

Schema contract (set in migration 006_add_row_audit_triggers):
  - id              BIGSERIAL PRIMARY KEY
  - event_id        UUID NOT NULL
  - table_name      TEXT NOT NULL
  - pk_id           TEXT          — primary-key value of the audited row
  - operation       CHAR(1)       — 'I'=INSERT | 'U'=UPDATE | 'D'=DELETE
  - actor_user_id   TEXT          — from GUC app.current_user_id
  - actor_role      TEXT          — from GUC app.current_user_role
  - correlation_id  TEXT          — from GUC app.correlation_id
  - before_data     JSONB         — OLD.* snapshot (NULL on INSERT)
  - after_data      JSONB         — NEW.* snapshot (NULL on DELETE)
  - changed_columns TEXT[]        — columns that changed (UPDATE only)
  - recorded_at     TIMESTAMPTZ   — clock_timestamp() at trigger fire time
"""
from sqlalchemy import (
    BigInteger, Column, CHAR, DateTime, Index, String, Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy import func
import uuid
from app.core.db_metadata import Base


class RowAuditLog(Base):
    """
    Immutable, database-level audit trail.

    One row is appended for every INSERT, UPDATE, or DELETE on every
    audited business table.  Rows are written by the fn_row_audit_log()
    trigger — never by application code.

    Usage:
        # Full history for a specific row
        rows = await session.execute(
            select(RowAuditLog)
            .where(RowAuditLog.table_name == "journal_entry")
            .where(RowAuditLog.pk_id == str(journal_entry_id))
            .order_by(RowAuditLog.recorded_at)
        )

        # All changes by a specific user
        rows = await session.execute(
            select(RowAuditLog)
            .where(RowAuditLog.actor_user_id == str(user_id))
            .order_by(RowAuditLog.recorded_at.desc())
            .limit(100)
        )
    """
    __tablename__ = "row_audit_log"

    # ------------------------------------------------------------------ #
    # Columns                                                             #
    # ------------------------------------------------------------------ #
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Monotonically increasing surrogate key — never reused.",
    )
    event_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
        comment="Unique event UUID — safe to expose in APIs.",
    )
    table_name = Column(
        Text,
        nullable=False,
        index=True,
        comment="Name of the audited table.",
    )
    pk_id = Column(
        Text,
        nullable=True,
        comment="Primary-key value of the changed row (TEXT covers UUID, int, string).",
    )
    operation = Column(
        CHAR(1),
        nullable=False,
        comment="'I'=INSERT | 'U'=UPDATE | 'D'=DELETE",
    )

    # Actor context — populated from PostgreSQL GUCs
    actor_user_id = Column(
        Text,
        nullable=True,
        index=True,
        comment="User ID from GUC app.current_user_id; NULL for background tasks.",
    )
    actor_role = Column(
        Text,
        nullable=True,
        comment="User role from GUC app.current_user_role.",
    )
    correlation_id = Column(
        Text,
        nullable=True,
        comment="Request correlation ID from GUC app.correlation_id.",
    )

    # Row snapshots
    before_data = Column(
        JSONB,
        nullable=True,
        comment="OLD row serialised to JSONB.  NULL on INSERT.",
    )
    after_data = Column(
        JSONB,
        nullable=True,
        comment="NEW row serialised to JSONB.  NULL on DELETE.",
    )
    changed_columns = Column(
        ARRAY(Text),
        nullable=True,
        comment="Column names whose value changed.  UPDATE only; NULL on INSERT/DELETE.",
    )

    # Timestamp — clock_timestamp() in trigger, not now() / transaction start
    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.clock_timestamp(),
        nullable=False,
        index=True,
        comment="Wall-clock time when the trigger fired; NOT the transaction start time.",
    )

    # ------------------------------------------------------------------ #
    # Indexes (mirror what migration creates; SQLAlchemy metadata only)  #
    # ------------------------------------------------------------------ #
    __table_args__ = (
        Index("idx_ral_table_pk",   "table_name", "pk_id"),
        Index("idx_ral_table_time", "table_name", "recorded_at"),
        Index("idx_ral_actor",      "actor_user_id"),
        Index("idx_ral_operation",  "operation"),
        Index("idx_ral_recorded",   "recorded_at"),
        Index("idx_ral_correl",     "correlation_id"),
        {
            "comment": (
                "Immutable, database-level audit trail populated by "
                "fn_row_audit_log() trigger.  Never write to this table "
                "from application code."
            )
        },
    )

    def __repr__(self) -> str:
        return (
            f"<RowAuditLog("
            f"id={self.id}, "
            f"op={self.operation}, "
            f"table={self.table_name}, "
            f"pk={self.pk_id}, "
            f"actor={self.actor_user_id}, "
            f"at={self.recorded_at}"
            f")>"
        )
