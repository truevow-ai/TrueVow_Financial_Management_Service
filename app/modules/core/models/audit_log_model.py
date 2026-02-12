"""Audit Log Model"""
from sqlalchemy import Column, String, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import uuid
from app.core.db_metadata import Base


class AuditLog(Base):
    """Audit log model for tracking all mutations"""
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # User ID from JWT/Clerk (spec field)
    actor_id = Column(UUID(as_uuid=True), nullable=True)  # Legacy field (maps to actor_user_id)
    actor_role = Column(String(50), nullable=True)  # User role (spec field)
    role = Column(String(50), nullable=True)  # Legacy field (maps to actor_role)
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, view, export, post, reverse, PAYROLL_SUBMIT, PAYROLL_APPROVE, etc.
    object_type = Column(String(100), nullable=False, index=True)  # journal_entry, gl_account, payroll_run, etc.
    object_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    before_json = Column(JSON, nullable=True)  # Old values (spec field); JSON for SQLite/Postgres compat
    after_json = Column(JSON, nullable=True)  # New values (spec field)
    before = Column(JSON, nullable=True)  # Legacy field (maps to before_json)
    after = Column(JSON, nullable=True)  # Legacy field (maps to after_json)
    reason = Column(Text, nullable=True)  # Reason for action (required on reject, recommended on approve)
    correlation_id = Column(String(100), nullable=True, index=True)  # Request correlation ID
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)  # Spec field
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)  # Legacy field (maps to created_at)
    
    __table_args__ = (
        Index("ix_audit_log_actor_created", "actor_user_id", "created_at"),
        Index("ix_audit_log_actor_timestamp", "actor_id", "timestamp"),
        Index("ix_audit_log_object", "object_type", "object_id"),
        Index("ix_audit_log_action_created", "action", "created_at"),
        # correlation_id uses index=True on column; do not duplicate here
        {"comment": "Audit log for all mutations and critical operations"},
    )
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, object_type={self.object_type}, object_id={self.object_id}, timestamp={self.timestamp})>"
